from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class DeleteHandOffTargetParams:
    # id is your identifier of choice for this hand-off target. Can be anything consisting
    # of letters, numbers, or any of the following characters: `_` `-` `+` `=`.
    id: str


def delete_hand_off_target(
    *, client: HttpClient, params: DeleteHandOffTargetParams
) -> None:
    _ = client.delete(
        path="hand-off-targets",
        body=params.to_dict(),
    )
