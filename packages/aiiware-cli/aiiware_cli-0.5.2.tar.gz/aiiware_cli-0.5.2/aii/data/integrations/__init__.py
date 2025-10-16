"""External integrations"""

from .web_search import SearchResult, WebSearchClient
from .mcp.client_manager import MCPClientManager
from .mcp.models import ToolCallResult

__all__ = ["WebSearchClient", "SearchResult", "MCPClientManager", "ToolCallResult"]
