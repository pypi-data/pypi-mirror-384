from ._http_client import HttpClient
from .tool import Tool


def create_tool(*, client: HttpClient, params: Tool) -> Tool:
    """create_tool creates a new tool.

    Note: requires a `Management` API key."""
    rsp = client.post(path="tools", body=params.to_dict())
    return Tool.from_dict(rsp)
