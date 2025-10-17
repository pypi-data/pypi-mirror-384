from typing import Optional, List
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._pagination import PaginationInfo
from .procedure import Procedure, ProcedureStatus

from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class ProcedureListParams:
    # cursor is used to retrieve the next/previous page of the list.
    cursor: Optional[str] = None

    # status is used to filter the list of procedures by status.
    status: Optional[ProcedureStatus] = None


@dataclass_json
@dataclass(frozen=True)
class ProcedureListResponse:
    # procedures contains the list of procedures.
    procedures: List[Procedure]

    # pagination contains the pagination-related information.
    pagination: PaginationInfo


def list_procedures(
    *, client: HttpClient, params: ProcedureListParams
) -> ProcedureListResponse:
    path = "procedures"
    if params.cursor is not None:
        path = f"{path}?cursor={params.cursor}"
    if params.status is not None:
        path = f"{path}?status={params.status}"

    rsp = client.get(path=path, body={})
    return ProcedureListResponse.from_dict(rsp)
