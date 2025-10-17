from typing import Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from .procedure import Procedure

from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class ProcedureLimitParams:
    # has_daily_limit identifies whether the procedure should have a limit
    has_daily_limit: bool

    # max_daily_conversations is the maximum number of conversations that
    # can use this procedure on a given day.
    max_daily_conversations: Optional[int] = 0


# set_procedure_limit updates the daily usage limit of a procedure.
def set_procedure_limit(
    *, client: HttpClient, procedure_id: str, params: ProcedureLimitParams
) -> Procedure:
    body = client.post(
        path=f"procedure/{procedure_id}/limit",
        body=params.to_dict(),
    )
    return Procedure.from_dict(body)
