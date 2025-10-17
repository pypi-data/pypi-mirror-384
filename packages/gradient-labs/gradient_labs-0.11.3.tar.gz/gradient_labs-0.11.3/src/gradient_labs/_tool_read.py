from ._http_client import HttpClient
from .tool import Tool


def read_tool(*, client: HttpClient, tool_id: str) -> Tool:
    """read_tool retrieves a new tool.
    Note: requires a `Management` API key."""
    rsp = client.get(
        path=f"tools/{tool_id}",
        body={},
    )
    return Tool.from_dict(rsp)
