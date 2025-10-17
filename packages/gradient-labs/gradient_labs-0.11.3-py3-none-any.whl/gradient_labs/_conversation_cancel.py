from typing import Optional
from datetime import datetime

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class CancelParams:
    # Timestamp optionally defines the time when the conversation was cancelled.
    # If not given, this will default to the current time.
    timestamp: Optional[datetime] = None

    # Reason optionally allows you to describe why this cancellation is happening.
    reason: Optional[str] = None


def cancel_conversation(
    *, client: HttpClient, conversation_id: str, params: CancelParams
) -> None:
    body = {}
    if params.timestamp is not None:
        body["timestamp"] = HttpClient.localize(params.timestamp)
    if params.reason is not None:
        body["reason"] = params.reason

    _ = client.put(
        f"conversations/{conversation_id}/cancel",
        body=body,
    )
