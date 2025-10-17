from typing import List
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._http_client import HttpClient
from .tool import Tool


@dataclass_json
@dataclass(frozen=True)
class ToolList:
    """ToolList is the response from the list_tools endpoint."""

    # tools contains the list of tools.
    tools: List[Tool]


def list_tools(*, client: HttpClient) -> List[Tool]:
    """list_tools retrieves all tools.
    Note: requires a `Management` API key."""
    rsp = client.get(
        path="tools",
        body=None,
    )

    rsp = ToolList.from_dict(rsp)
    return rsp.tools
