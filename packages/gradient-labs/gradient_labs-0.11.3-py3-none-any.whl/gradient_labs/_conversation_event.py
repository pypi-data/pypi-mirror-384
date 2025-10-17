from typing import Optional
from datetime import datetime

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from .conversation import ConversationEventType, ParticipantType
from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class EventParams:
    # type identifies the type of event (see: ConversationEventType).
    type: ConversationEventType

    # participant_id identifies the message sender.
    participant_id: str

    # participant_type identifies the type of participant who sent this message.
    participant_type: ParticipantType

    # MessageID optionally identifies the message that this event relates to
    message_id: Optional[str] = None

    # timestamp optionally defines the time when the conversation was assigned.
    # If not given, this will default to the current time.
    timestamp: Optional[datetime] = None

    # IdempotencyKey optionally enables you to safely retry requests
    idempotency_key: Optional[str] = None

    # Body optionally allows adding content (text) to the event. This is
    # required for the
    body: Optional[str] = None


def add_conversation_event(
    *, client: HttpClient, conversation_id: str, params: EventParams
) -> None:
    body = {
        "type": params.type,
        "participant_id": params.participant_id,
        "participant_type": params.participant_type,
    }
    if params.message_id is not None:
        body["message_id"] = params.message_id
    if params.timestamp is not None:
        body["timestamp"] = HttpClient.localize(params.timestamp)
    if params.idempotency_key is not None:
        body["idempotency_key"] = params.idempotency_key
    if params.body is not None:
        body["body"] = params.body

    _ = client.post(
        path=f"conversations/{conversation_id}/events",
        body=body,
    )
