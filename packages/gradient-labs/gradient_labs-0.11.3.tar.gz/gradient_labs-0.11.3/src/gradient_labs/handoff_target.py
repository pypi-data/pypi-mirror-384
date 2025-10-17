from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass(frozen=True)
class HandOffTarget:
    # ID is your identifier of choice for this hand-off target. Can be anything consisting
    # of letters, numbers, or any of the following characters: `_` `-` `+` `=`.
    id: str

    # name is the hand-off target’s name.
    name: str
