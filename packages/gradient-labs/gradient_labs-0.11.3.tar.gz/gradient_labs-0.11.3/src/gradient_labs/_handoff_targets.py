from typing import List

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from .handoff_target import HandOffTarget
from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class HandOffTargets:
    targets: List[HandOffTarget]


def list_handoff_targets(*, client: HttpClient) -> HandOffTargets:
    rsp = client.get(
        path="hand-off-targets",
        body={},
    )
    return HandOffTargets.from_dict(rsp)
