import logging
logger = logging.getLogger(__name__)

import json
from anthropic.types.beta import BetaMessage

from cua.ai.tool_box import ToolBox
from cua.db.models import DB_Step, DB_ToolCall, ToolCallStatus, ContentType, StopReason
from cua.ai.client import anthropic_beta_request


async def send_request(steps: list[DB_Step], 
                       tool_box: ToolBox,
                       system_prompt: str,
                       instructions: str) -> DB_Step:
    if len(steps) == 0:
        raise ValueError("No agent loop steps provided")
    
    # Generate request messages including images for the last n_images_to_keep steps
    messages = _generate_messages(steps)
    
    # Send request
    raw_response: BetaMessage = await anthropic_beta_request(
            messages=messages,
            # kwargs
            # model="claude-sonnet-4-20250514",
            # model="claude-opus-4-1-20250805",
            model="claude-haiku-4-5",
            max_tokens=5000,
            tools=await tool_box.get_anthropic_tool_definitions(),
            betas=["computer-use-2025-01-24", 
                   "token-efficient-tools-2025-02-19", 
                   "interleaved-thinking-2025-05-14", 
                   "context-management-2025-06-27",
                   "mcp-client-2025-04-04"],
            thinking={"type": "enabled", "budget_tokens": 3000},
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            context_management={
                "edits": [
                    {
                        "type": "clear_tool_uses_20250919",
                        # Trigger clearing when threshold is exceeded
                        "trigger": {
                            "type": "tool_uses",
                            "value": 25
                        },
                        # Number of tool uses to keep after clearing
                        "keep": {
                            "type": "tool_uses",
                            "value": 15
                        },
                        # Exclude these tools from being cleared
                        "exclude_tools": ["web_search", "memory"],
                        "clear_tool_inputs": True
                    }
                ]
            },
            # mcp_servers=[
            #     {
            #         "type": "url",
            #         "url": "https://mcp.hunter.io/mcp",
            #         "name": "hunter-mcp",
            #         "authorization_token": settings.HUNTER_API_KEY
            #     }
            # ]
        )
    
    new_step = _parse_raw_response(raw_response, steps)
    
    return new_step

def _generate_messages(steps: list[DB_Step]) -> list[dict]:
    # Generate request messages including images for the last n_images_to_keep steps
    messages = []
    
    # # inject notes.md
    # notes_text = ""
    # lines = self._agent.notes.split('\n') if self._agent.notes else []
    # for i, line in enumerate(lines):
    #     notes_text += f"{i+1}: {line}\n"
    # notes_text = f"<injected_message>\nContents of notes.md:\n```\n{notes_text}\n```\n</injected_message>"
    # messages.append({"role": "user", "content": [{"type": "text", "text": notes_text}]})
    
    # create request messages from steps
    messages.extend(_steps_to_messages(steps, n_images_to_keep=20))

    # add cache control to last content block of last message
    try:
        messages[-1]["content"][-1]["cache_control"] = {"type": "ephemeral"}
    except (IndexError, KeyError):
        logger.error("Unable to add cache control to last message")

    return messages


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def _steps_to_messages(steps: list[DB_Step], n_images_to_keep: int = 20) -> list[dict]:
    messages = []
    
    n_steps = len(steps)
    for i, db_agent_loop_step in enumerate(steps):
        # Add response messages
        if db_agent_loop_step.raw_response:
            messages.extend(db_agent_loop_step.raw_response)
        
        # Generate and add request messages
        include_images = i >= n_steps - n_images_to_keep
        messages.extend(_generate_request_messages(db_agent_loop_step, include_images))

    return messages


def _generate_request_messages(db_agent_loop_step: DB_Step, include_images: bool = True) -> list:
    req_content = []
    
    # Add tool results to request_content
    for tool_call in db_agent_loop_step.tool_calls:
        req_content.append(_tool_call_to_message_content(tool_call, include_images))
    
    # Add user message to request_content
    if db_agent_loop_step.request_content:
        for content_block in db_agent_loop_step.request_content.content_list:
            if content_block.type == ContentType.TEXT:
                req_content.append({"type": "text", "text": content_block.content})
            elif content_block.type == ContentType.IMAGE:
                req_content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": content_block.content}})

    return [{"role": "user", "content": req_content}]


def _tool_call_to_message_content(db_tool_call: DB_ToolCall, include_images: bool = True) -> dict:
    tool_content = []
    
    if db_tool_call.status == ToolCallStatus.PENDING:
        tool_content.append({"type": "text", "text": "Interrupted: Tool call was aborted"})
    else:
        if db_tool_call.output_text:
            tool_content.append({"type": "text", "text": db_tool_call.output_text})
        if include_images and db_tool_call.output_base64_png_list:
            for base64_png in db_tool_call.output_base64_png_list:
                tool_content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64_png}})
            
    return {"type": "tool_result", "tool_use_id": db_tool_call.call_id, "content": tool_content}


def _parse_raw_response(raw_response: BetaMessage, db_agent_loop_steps: list[DB_Step]) -> DB_Step:
    # Parse response
    stop_reason = None
    if raw_response.stop_reason == "tool_use":
        stop_reason = StopReason.TOOL_CALLS
    elif raw_response.stop_reason == "end_turn":
        stop_reason = StopReason.END_TURN
    else:
        logger.warning(f"Unexpected stop reason: {raw_response.stop_reason}")
        stop_reason = StopReason.END_TURN
    
    content = []
    text = ""
    thinking_text = ""
    tool_calls = []
    
    for block in raw_response.content:
        # Workaround for Anthropic bug (response might contain empty text blocks which are not valid for a subsequent request)
        if block.type == "text" and block.text == "":
            logger.warning(f"Invalid text block with empty text: {block}")
        else:
            content.append(block.model_dump(exclude_unset=True))
        
        if block.type == "text":
            text += block.text
        elif block.type == "thinking":
            thinking_text += block.thinking
        elif block.type == "tool_use":
            tool_call = DB_ToolCall(
                call_id=block.id,
                name=block.name,
                input=json.dumps(block.input),
                output_text="Tool call was aborted."
            )
            tool_calls.append(tool_call)

    # Create new step object
    new_step = DB_Step(
        agent_loop_id=db_agent_loop_steps[0].agent_loop_id,
        sequence=db_agent_loop_steps[-1].sequence + 1,
        raw_response=[{"role": "assistant", "content": content}],
        stop_reason=stop_reason,
        response_text=text if len(text) > 0 else None,
        response_thinking_text=thinking_text if len(thinking_text) > 0 else None,
        tool_calls=tool_calls,
    )
    
    return new_step