import logging
logger = logging.getLogger(__name__)

from anthropic.types.beta import BetaMessage
import httpx

from cua.config import get_config

async def anthropic_beta_request(messages: list, **kwargs) -> BetaMessage:
    config = get_config()
    # make http request
    response = await httpx.AsyncClient(timeout=10 * 60.0).post(
        config.backend_api_base_url + "/v2/llm/anthropic-beta",
        json={
            "agent_instance_id": config.agent_instance_id,
            "secret_key": config.secret_key,
            "messages": messages,
            "kwargs": kwargs
        }
    )
    response.raise_for_status()
    return BetaMessage.model_validate(response.json())