from _typeshed import Incomplete
from gllm_inference.schema.enums import ActivityType as ActivityType, WebSearchKey as WebSearchKey
from pydantic import BaseModel
from typing import Literal

WEB_SEARCH_VISIBLE_FIELDS: Incomplete

class Activity(BaseModel):
    """Base schema for any activity.

    Attributes:
        type (str): The type of activity being performed.
    """
    type: str

class MCPListToolsActivity(Activity):
    """Schema for listing tools in MCP.

    Attributes:
        server_name (str): The name of the MCP server.
        tools (list[dict[str, str]] | None): The tools in the MCP server.
        type (str): The type of activity being performed.
    """
    type: Literal[ActivityType.MCP_LIST_TOOLS]
    server_name: str
    tools: list[dict[str, str]] | None

class MCPCallActivity(Activity):
    """Schema for MCP tool call.

    Attributes:
        server_name (str): The name of the MCP server.
        tool_name (str): The name of the tool.
        args (dict[str, str]): The arguments of the tool.
        type (str): The type of activity being performed.
    """
    type: Literal[ActivityType.MCP_CALL]
    server_name: str
    tool_name: str
    args: dict[str, str]

class WebSearchActivity(Activity):
    """Schema for web search tool call.

    Attributes:
        type (str): The type of activity being performed.
        pattern (str): The pattern of the web search.
        url (str): The URL of the page.
        query (str): The query of the web search.
        sources (list[dict[str, str]] | None): The sources of the web search.
    """
    type: Literal[ActivityType.FIND_IN_PAGE, ActivityType.OPEN_PAGE, ActivityType.SEARCH]
    url: str | None
    pattern: str | None
    query: str | None
    sources: list[dict[str, str]] | None
    def model_dump(self, *args, **kwargs) -> dict[str, str]:
        """Serialize the activity for display.

        Returns:
            dict[str, str]: The serialized activity.
        """
