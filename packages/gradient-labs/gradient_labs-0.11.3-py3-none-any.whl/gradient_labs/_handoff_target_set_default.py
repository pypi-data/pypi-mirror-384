from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._http_client import HttpClient
from .conversation import ConversationChannel


@dataclass_json
@dataclass(frozen=True)
class SetDefaultHandOffTargetParams:
    # id is your identifier of choice for this hand-off target. Can be anything consisting
    # of letters, numbers, or any of the following characters: `_` `-` `+` `=`.
    id: str

    # channel is the conversation channel for which to set the default hand-off target.
    channel: ConversationChannel


def set_default_hand_off_target(
    *, client: HttpClient, params: SetDefaultHandOffTargetParams
) -> None:
    _ = client.put(
        path="hand-off-targets/default",
        body=params.to_dict(),
    )
