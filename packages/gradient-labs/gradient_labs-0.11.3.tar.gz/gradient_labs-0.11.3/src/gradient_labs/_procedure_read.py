from ._http_client import HttpClient
from .procedure import Procedure


def read_procedure(*, client: HttpClient, procedure_id: str) -> Procedure:
    """read_procedure reads a procedure.
    Note: requires a `Management` API key."""
    body = client.get(
        path=f"procedure/{procedure_id}",
        body={},
    )
    return Procedure.from_dict(body)
