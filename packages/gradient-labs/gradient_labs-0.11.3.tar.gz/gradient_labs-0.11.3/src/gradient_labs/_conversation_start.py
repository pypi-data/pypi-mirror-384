from typing import Optional, Dict, Any
from datetime import datetime

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ._http_client import HttpClient
from .conversation import ParticipantType, ConversationChannel, Conversation


@dataclass_json
@dataclass(frozen=True)
class StartConversationParams:
    # id uniquely identifies the conversation.
    #
    # Can be anything consisting of letters, numbers, or any of the following
    # characters: _ - + =.
    #
    # Tip: use something meaningful to your business (e.g. a ticket number).
    id: str

    # customer_id uniquely identifies the customer. Used to build historical
    # context of conversations the agent has had with this customer.
    customer_id: str

    # channel represents the way a customer is getting in touch. It will be used
    # to determine how the agent formats responses, etc.
    channel: ConversationChannel

    # assignee_id optionally identifies who the conversation is assigned to.
    assignee_id: Optional[str] = None

    # assignee_type optionally identifies which type of participant is currently
    # assigned to respond. Set this to ParticipantTypeAIAgent to assign the conversation
    # to the Gradient Labs AI when starting it.
    assignee_type: Optional[ParticipantType] = None

    # metadata is arbitrary metadata that will be attached to the conversation.
    # It will be passed along with webhooks so can be used as action parameters.
    metadata: Optional[Any] = None

    # created optionally defines the time when the conversation started.
    # If not given, this will default to the current time.
    created: Optional[datetime] = None

    # resources is an arbitrary object attached to the conversation and available to the AI agent
	# during the conversation. You can also use resources as parameters for your tools.
    resources: Optional[Dict[str, Any]] = None


def start_conversation(
    *, client: HttpClient, params: StartConversationParams
) -> Conversation:
    body = {
        "id": params.id,
        "customer_id": params.customer_id,
        "channel": params.channel.value,
    }
    if params.metadata is not None:
        body["metadata"] = params.metadata
    if params.created is not None:
        body["created"] = HttpClient.localize(params.created)
    if params.resources is not None:
        body["resources"] = params.resources

    rsp = client.post(
        path="conversations",
        body=body,
    )
    return Conversation.from_dict(rsp)
