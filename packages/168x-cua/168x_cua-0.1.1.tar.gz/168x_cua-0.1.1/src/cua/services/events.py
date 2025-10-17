import logging
logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession

from cua.db.models import DB_Event

from cua_protocol.schemas import OutboundMessageEvent, ToolCallEvent, ToolResultEvent

async def add_outbound_message_event(text: str, session: AsyncSession):
    logger.info(f"Adding outbound message event: {text}")
    event = OutboundMessageEvent(text=text)
    db_event = DB_Event(event=event)
    session.add(db_event)
    

async def add_tool_call_event(tool_call_event: ToolCallEvent, session: AsyncSession):
    logger.info(f"Adding tool call event: {tool_call_event}")
    db_event = DB_Event(event=tool_call_event)
    session.add(db_event)


async def add_tool_result_event(tool_result_event: ToolResultEvent, session: AsyncSession):
    logger.info(f"Adding tool result event: {tool_result_event}")
    db_event = DB_Event(event=tool_result_event)
    session.add(db_event)
