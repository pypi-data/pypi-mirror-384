from typing import Optional
from datetime import datetime

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class RatingParams:
    # type identifies the type of survey sent to customers.
    type: str

    # value is the rating value that was submitted by the customer.
    # It must be a value between [MinValue, MaxValue].
    value: int

    # max_value is the maximum value in the rating scale.
    max_value: int

    # MinValue is the minimum value of the rating scale.
    min_value: int

    # Comments optionally submits any free-text that was submitted by the
    # customer alongside their rating.
    comments: Optional[str] = None

    # Timestamp optionally defines the time when the conversation was rate.
    # If not given, this will default to the current time.
    timestamp: Optional[datetime] = None


def rate_conversation(
    *, client: HttpClient, conversation_id: str, params: RatingParams
) -> None:
    """rate_conversation submits a customer (CSAT) rating for a conversation."""
    body = {
        "type": params.type,
        "value": params.value,
        "max_value": params.max_value,
        "min_value": params.min_value,
    }
    if params.comments is not None:
        body["comments"] = params.comments
    if params.timestamp is not None:
        body["timestamp"] = HttpClient.localize(params.timestamp)

    _ = client.put(
        path=f"conversations/{conversation_id}/rate",
        body=body,
    )
