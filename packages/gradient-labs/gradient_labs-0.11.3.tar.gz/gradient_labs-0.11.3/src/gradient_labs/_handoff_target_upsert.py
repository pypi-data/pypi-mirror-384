from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class UpsertHandOffTargetParams:
    # id is your identifier of choice for this hand-off target. Can be anything consisting
    # of letters, numbers, or any of the following characters: `_` `-` `+` `=`.
    id: str

    # name is the hand-off target’s name. This cannot be nil.
    name: str


def upsert_hand_off_target(
    *, client: HttpClient, params: UpsertHandOffTargetParams
) -> None:
    _ = client.post(
        path="hand-off-targets",
        body=params.to_dict(),
    )
