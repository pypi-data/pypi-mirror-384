import logging
logger = logging.getLogger(__name__)

import json
import httpx
from pydantic import BaseModel, Field

from cua.ai.tool_box import Tool, ToolResult


class LinkedInArgs(BaseModel):
    url: str = Field(description="The URL of the LinkedIn profile to lookup")
    # realtime: bool = Field(description="Whether to return the realtime profile or the cached profile", default=False)

class LinkedInTool(Tool):
    def __init__(self):
        super().__init__(
            name="linkedin_person_lookup",
            description="Looks up a LinkedIn profile and returns the person's full profile",
            input_model=LinkedInArgs,
        )

    def get_ui_tool_name(self, args) -> str:
        return f"LinkedIn lookup - {args.url}"

    async def __call__(self, args: LinkedInArgs) -> ToolResult:
        # try:            
        #     # Make API request
        #     async with httpx.AsyncClient(timeout=60.0) as client:
        #         response = await client.get(
        #             "https://api.crustdata.com/screener/person/enrich",
        #             headers={
        #                 "Authorization": f"Bearer 8ced988c6f5a872c86d93b0dcbc17752b51d9923",
        #             },
        #             params={
        #                 "linkedin_profile_url": args.url,
        #                 "enrich_realtime": "true",
        #                 "force_fetch": "true",
        #             }
        #         )
                
        #         # Raise exception for error status codes
        #         response.raise_for_status()
                
        #         # Parse and return the response
        #         result_data = response.json()
        #         result_text = json.dumps(result_data)
                
        #         return ToolResult(text=result_text)
                
        # except httpx.HTTPStatusError as e:
        #     error_msg = f"API request failed with status {e.response.status_code}: {e.response.text}"
        #     logger.error(error_msg)
        #     return ToolResult(text=f"Error: {error_msg}")
        # except Exception as e:
        #     error_msg = f"Failed to lookup LinkedIn profile: {str(e)}"
        #     logger.error(error_msg)
        #     return ToolResult(text=f"Error: {error_msg}")
        
        return ToolResult(text="mock data for linkedin_person_lookup tool call")