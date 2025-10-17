from typing import Optional, Any, List

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class Argument:
    # name is the parameter name.
    name: str

    # value is the value of the argument.
    # It is a string here, but it will be converted to the
    # appropriate type when the tool is called.
    value: str


@dataclass_json
@dataclass(frozen=True)
class ToolExecuteParams:
    # id identifies the tool.
    id: str

    # arguments to execute the tool with.
    arguments: Optional[List[Argument]] = field(default_factory=lambda: [])


@dataclass_json
@dataclass(frozen=True)
class ToolExecuteResult:
    # id identifies the tool.
    id: str

    # result is the JSON-encoded result of the tool execution.
    result: Any


def execute_tool(*, client: HttpClient, params: ToolExecuteParams) -> ToolExecuteResult:
    """execute_tool executes a tool.

    Note: requires a `Management` API key."""
    rsp = client.post(path=f"tools/{params.id}/execute", body=params.to_dict())
    return ToolExecuteResult.from_dict(rsp)
