from typing import Any
from ._http_client import HttpClient


def add_resource(
    *, client: HttpClient, conversation_id: str, name: str, resource: Any
) -> None:
    """
    AddResource adds (or updates) a resource to the conversation (e.g. the
    customer's order details) so the AI agent can handle customer-specific
    queries.

    A resource can be any JSON document, as long it is smaller than 1MB. There
    are no strict requirements on the format/structure of the document, but we
    recommend making attribute names as descriptive as possible.

    Over time, the AI agent will learn the structure of your resources - so while
    it's fine to add new attributes, you may want to consider using new resource
    names when removing attributes or changing the structure of your resources
    significantly.

    Resource names are case-insensitive and can be anything consisting of letters,
    numbers, or any of the following characters: _ - + =.

    Names should be descriptive handles that are the same for all conversations
    (e.g. "order-details" and "user-profile") not unique identifiers.
    """
    _ = client.put(
        path=f"conversations/{conversation_id}/resources/{name}",
        body=resource,
    )
