from typing import Optional, Dict, Any
from datetime import datetime

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._http_client import HttpClient
from .conversation import ParticipantType


@dataclass_json
@dataclass(frozen=True)
class ResumeParams:
    # assignee_type identifies the type of participant that this conversation is
    # being assigned to. Set this to ParticipantTypeAIAgent to assign the conversation
    # to the Gradient Labs AI agent.
    assignee_type: ParticipantType

    # assignee_id optionally identifies the specific user that the conversation
    # is being assigned to.
    assignee_id: Optional[str] = None

    # Timestamp optionally defines the time when the conversation was assigned.
    # If not given, this will default to the current time.
    timestamp: Optional[datetime] = None

    # reason optionally allows you to describe why this assignment is happening.
    reason: Optional[str] = None

    # resources is an arbitrary object attached to the conversation and available to the AI agent
	# during the conversation. You can also use resources as parameters for your tools.
    resources: Optional[Dict[str, Any]] = None


def resume_conversation(
    *, client: HttpClient, conversation_id: str, params: ResumeParams
) -> None:
    """resume_conversation re-opens a conversation that was previously finished."""
    body = {"assignee_type": params.participant_type.value}
    if params.assignee_id:
        body["assignee_id"] = params.assignee_id
    if params.timestamp:
        body["timestamp"] = HttpClient.localize(params.timestamp)
    if params.resources is not None:
        body["resources"] = params.resources

    _ = client.put(
        path=f"conversations/{conversation_id}/resume",
        body=params.to_dict(),
    )
