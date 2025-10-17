from ._http_client import HttpClient


def delete_tool(*, client: HttpClient, tool_id: str) -> None:
    """delete_tool deletes a tool. Note: will not allow to delete a tool used in an active procedure.

    Note: requires a `Management` API key."""
    _ = client.delete(
        path=f"tools/{tool_id}",
        body={},
    )
