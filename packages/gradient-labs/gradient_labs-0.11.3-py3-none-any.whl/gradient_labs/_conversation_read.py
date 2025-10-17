from typing import Optional

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._http_client import HttpClient
from .conversation import Conversation


@dataclass_json
@dataclass(frozen=True)
class ReadParams:
    # SupportPlatform is the name of the support platform where the
    # conversation was started (e.g. Intercom).
    #
    # Leave empty if the conversation was started via the Gradient
    # Labs API.
    support_platform: Optional[str] = None


def read_conversation(
    *, client: HttpClient, conversation_id: str, params: ReadParams
) -> Conversation:
    path = f"conversations/{conversation_id}/read"
    if params.support_platform:
        path += "?support_platform={params.support_platform}"

    rsp = client.get(
        path=path,
        body=None,
    )
    return Conversation.from_dict(rsp)
