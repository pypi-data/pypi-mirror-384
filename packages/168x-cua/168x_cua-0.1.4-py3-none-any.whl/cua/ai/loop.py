import logging

from cua.ai.llm_adapter import anthropic_adpater
logger = logging.getLogger(__name__)


import asyncio
from pydantic import BaseModel, ConfigDict
import httpx
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, delete

from cua.config import get_config
from cua.state import state, Model

from cua.db.database import get_session
from cua.db.models import DB_Step, DB_ToolCall, DB_Event, ContentBlock, ContentType, DB_AgentLoop, RequestContent, StopReason, ToolCallStatus
from cua.ai.tool_box import ToolBox
from cua_protocol import CheckInRequest, CheckInResponse, ToolCallEvent, ToolResultEvent
from cua.services.events import add_outbound_message_event, add_tool_call_event, add_tool_result_event
from cua.ai.tools.linkedin_crustdata import LinkedInTool
from cua.ai.tools.computer_use import ComputerUseTool


async def run_loop():
    # load all steps
    steps = await _load_steps()
        
    tool_box = ToolBox()
    tool_box.register_tool(LinkedInTool())
    tool_box.register_tool(ComputerUseTool())
        
    while True:
        await checkin(steps, tool_box)
        await llm_call(steps, tool_box)

        async for tool in get_next_tool_call(steps):
            await checkin(steps, tool_box)
            await run_tool_call(tool, tool_box)
        
        # need to refresh latest step since tool calls may have modified it
        await refresh_latest_step(steps)
        
        await clean_up_context(steps)
            

async def _load_steps() -> list[DB_Step]:
    main_loop_id = 0 # default for main loop
    
    async with get_session() as session:
        # check if loop exists, if not, create it
        result = await session.execute(
            select(DB_AgentLoop)
            .where(DB_AgentLoop.id == main_loop_id))
        loop = result.scalar_one_or_none()
        if loop is None:
            loop = DB_AgentLoop(id=main_loop_id, name="MainLoop")
            session.add(loop)
            await session.commit()
    
        # count steps
        from sqlalchemy import func
        result = await session.execute(
            select(func.count())
            .select_from(DB_Step)
            .where(DB_Step.agent_loop_id == main_loop_id))
        step_count = result.scalar()
        
        # if no steps, create initial step
        if step_count == 0:
            initial_step = DB_Step(agent_loop_id=main_loop_id, sequence=1, stop_reason=StopReason.END_TURN)
            session.add(initial_step)
            await session.commit()
        
        # load all steps
        result = await session.execute(
            select(DB_Step)
            .where(DB_Step.agent_loop_id == main_loop_id)
            .order_by(DB_Step.sequence))
        steps = result.scalars().all()
            
    return steps
    
    
async def refresh_latest_step(steps: list[DB_Step]):
    async with get_session() as session:
        latest_step = await session.get(DB_Step, steps[-1].id)
        if latest_step:
            steps[-1] = latest_step


async def checkin(steps: list[DB_Step], tool_box: ToolBox):
    # Make a long poll checkin request
    checkin_response = await _long_poll_checkin(steps)
    
    # update system prompt and instructions
    async with state.transaction():
        state.data.system_prompt = checkin_response.system_prompt or "You are a helpful assistant."
        state.data.instructions = checkin_response.instructions
    
    # append new messages to request content
    latest_step = steps[-1]
    request_content = latest_step.request_content or RequestContent(content_list=[])
    latest_new_message_updated_at = state.data.latest_message_updated_at or datetime(1970, 1, 1, tzinfo=timezone.utc)
    for new_message in checkin_response.new_messages:
        new_content_block = ContentBlock(type=ContentType.TEXT, content=new_message.text)
        request_content.content_list.append(new_content_block)
        latest_new_message_updated_at = max(latest_new_message_updated_at, new_message.updated_at)
    latest_step.request_content = request_content
    
    # persist changes to database
    async with get_session() as session:
        await session.merge(latest_step)
        await session.commit()
        
    # update state.data.latest_message_updated_at
    async with state.transaction():
        state.data.latest_message_updated_at = latest_new_message_updated_at
    

async def _long_poll_checkin(steps: list[DB_Step]):
    await_new_message = True
    
    if steps and steps[-1].stop_reason != StopReason.END_TURN:
        await_new_message = False
    
    # long poll loop until run is True
    while True:
        try:
            checkin_response = await _send_checkin_request(await_new_message)
        except Exception as e:
            logger.warning(f"Error sending checkin request: {e}", exc_info=True)
            await asyncio.sleep(1.0)
            continue
        
        if await_new_message and len(checkin_response.new_messages) == 0:
            continue
        
        if not checkin_response.run:
            continue
        
        return checkin_response
    
async def _send_checkin_request(await_new_message: bool):
    config = get_config()
    
    # get all events
    async with get_session() as session:
        result = await session.execute(
            select(DB_Event))
        db_events = result.scalars().all()
        events = [db_event.event for db_event in db_events]
        event_ids = [db_event.id for db_event in db_events]
    
    request = CheckInRequest(agent_instance_id=config.agent_instance_id, 
                             secret_key=config.secret_key, 
                             last_updated_at=state.data.latest_message_updated_at, 
                             await_new_message=await_new_message,
                             events=events)
    
    async with httpx.AsyncClient(timeout=40.0) as client:
        # logger.info(f"Sending checkin request: {request.model_dump(mode='json')}")
        response = await client.post(
            url = f"{config.backend_api_base_url}/v2/agent-comm/check-in",
            json=request.model_dump(mode="json")
        )
        
        # Check response status
        response.raise_for_status()
        
        # Log raw response for debugging
        logger.debug(f"Checkin response status: {response.status_code}. Reponse text: {response.text}")
    
    # if success, delete only the events that were sent in this request
    if response.status_code == 200 and event_ids:
        async with get_session() as session:
            await session.execute(delete(DB_Event).where(DB_Event.id.in_(event_ids)))
            await session.commit()
    
    return CheckInResponse.model_validate(response.json())


# ------------------------------------------------------------
# LLM call
# ------------------------------------------------------------

async def llm_call(steps: list[DB_Step], tool_box: ToolBox):
    match state.data.model:
        case Model.CLAUDE_SONNET_4_5:
            logger.info(f"Sending LLM request.")
            new_step = await anthropic_adpater.send_request(steps, tool_box, state.data.system_prompt, state.data.instructions)
            logger.info(f"Received new step: {new_step}")
        case _:
            raise ValueError(f"Unsupported model: {state.data.model}")
    
    async with get_session() as session:
        # add new step
        steps.append(new_step)
        session.add(new_step)
        
        # add outbound message event
        if new_step.stop_reason == StopReason.END_TURN and new_step.response_text:
            await add_outbound_message_event(new_step.response_text, session)
        
        await session.commit()

# ------------------------------------------------------------
# Tool call
# ------------------------------------------------------------

async def get_next_tool_call(steps: list[DB_Step]):
    """
    Async generator that yields pending tool calls from the last step.
    
    Args:
        steps: List of DB_Step objects
        
    Yields:
        DB_ToolCall objects with status PENDING
    """
    if not steps:
        return
    
    # Get the last step
    last_step = steps[-1]
    
    # Yield tool calls with status PENDING
    for tool_call in last_step.tool_calls:
        if tool_call.status == ToolCallStatus.PENDING:
            yield tool_call

async def run_tool_call(tool_call: DB_ToolCall, tool_box: ToolBox):
    logger.info(f"Running tool call: {tool_call.name}")
    tool = tool_box.get_tool(tool_call.name)
    
    async with get_session() as session:
        # merge tool call to session
        tool_call = await session.merge(tool_call)
    
        # If tool is not found, set error and commit
        if tool is None:
            tool_call.output_text = f"Error: Unknown tool: {tool_call.name}"
            tool_call.status = ToolCallStatus.ERROR
            
            # Emit tool call event
            await add_tool_call_event(ToolCallEvent(tool_name=tool_call.name, 
                                                    tool_args=tool_call.input, 
                                                    tool_call_title="Unknown tool: {tool_call.name}"), session)
            
            # Emit tool result event
            await add_tool_result_event(ToolResultEvent(tool_outcome="unknown_tool", 
                                                        tool_output_text=tool_call.output_text, 
                                                        tool_output_base64_png_list=[]), session)
            
            # commit
            await session.commit()
            
            return
        
        # parse input
        args = tool.input_model.model_validate_json(tool_call.input)
        
        # get tool call title
        tool_call_title = tool.get_ui_tool_name(args)
        
        # Emit tool call start event and set status to running
        await add_tool_call_event(ToolCallEvent(tool_name=tool_call.name, 
                                                tool_args=tool_call.input, 
                                                tool_call_title=tool_call_title), session)
        tool_call.status = ToolCallStatus.RUNNING
        await session.commit()
        
        # Run tool
        try:
            tool_result = await tool(args)
        except Exception as e:
            tool_call.output_text = f"Error: {e}"
            tool_call.status = ToolCallStatus.ERROR
            
            # Emit tool result event
            await add_tool_result_event(ToolResultEvent(tool_outcome="error", 
                                                        tool_output_text=tool_call.output_text, 
                                                        tool_output_base64_png_list=[]), session)
            
            await session.commit()
            return
        
        tool_call.output_text = tool_result.text
        tool_call.output_base64_png_list = tool_result.base64_png_list or []
        tool_call.status = ToolCallStatus.SUCCESS
        
        # Emit tool result event
        await add_tool_result_event(ToolResultEvent(tool_outcome="success", 
                                                    tool_output_text=tool_call.output_text, 
                                                    tool_output_base64_png_list=[]), session)
        
        await session.commit()
        
        
# ------------------------------------------------------------
# Clean up context
# ------------------------------------------------------------
    
n_images_to_keep = 10
        
async def clean_up_context(steps: list[DB_Step]):
    n_retained = 0
    async with get_session() as session:
        for i in range(len(steps) - 1, -1, -1):
            n_images_in_step = _number_of_images_in_step(steps[i])
            
            # If we can still keep more images -> keep, and increase n_retained
            if n_retained < n_images_to_keep:
                n_retained += n_images_in_step
                
            # If we can't keep more images and step has images -> remove images
            elif n_images_in_step > 0:
                steps[i] = await session.merge(steps[i])
                _remove_images_from_step(steps[i])
        
        await session.commit()
            
def _number_of_images_in_step(step: DB_Step) -> int:
    n_images = 0
    if step.request_content and step.request_content.content_list:
        for content_block in step.request_content.content_list:
            if content_block.type == ContentType.IMAGE:
                n_images += 1
    
    for tool_call in step.tool_calls:
        if tool_call.output_base64_png_list:
            n_images += len(tool_call.output_base64_png_list)
        
    return n_images

def _remove_images_from_step(step: DB_Step):
    # Remove images from request content
    if step.request_content and step.request_content.content_list:
        step.request_content.content_list = [
            content_block for content_block in step.request_content.content_list
            if content_block.type != ContentType.IMAGE
        ]
    
    # Remove images from tool call outputs
    for tool_call in step.tool_calls:
        if tool_call.output_base64_png_list:
            tool_call.output_base64_png_list = []