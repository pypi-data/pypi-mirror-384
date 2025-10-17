from typing import Optional
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from marshmallow import fields
from typing import Any, Dict


class ParticipantType(str, Enum):
    """A participant type identifies the type of user who has
    sent a message in a conversation."""

    CUSTOMER: str = "Customer"
    HUMAN_AGENT: str = "Agent"
    AI_AGENT: str = "AI Agent"
    BOT: str = "Bot"


class ConversationChannel(str, Enum):
    """A channel identifies how the customer has gotten
    in touch with customer support."""

    EMAIL: str = "email"
    WEB: str = "web"


class AttachmentType(str, Enum):
    """An attachment type identifies the type of file
    that a customer has uploaded into the conversation."""

    IMAGE: str = "image"
    FILE: str = "file"


class ConversationEventType(str, Enum):
    """ConversationEventType describes an event that occurred within the conversation."""

    # INTERNAL_NOTE means that an internal note has been added to the conversation.
    INTERNAL_NOTE: str = "internal-note"

    # JOIN means the customer or human agent joined the
    # conversation.
    JOIN: str = "join"

    # LEAVE means the customer or human agent left the
    # conversation.
    LEAVE: str = "leave"

    # DELIVERED means that a message has been delivered
    # to a participant
    DELIVERED: str = "delivered"

    # MESSAGE_READ means that a message has been read
    # by the participant it was delivered to
    MESSAGE_READ: str = "read"

    # TYPING means the customer or human agent started typing.
    TYPING: str = "typing"


@dataclass_json
@dataclass(frozen=True)
class Conversation:
    """A conversation is the primary way that a customer
    talks to our AI agent.
    """

    id: str
    customer_id: str
    channel: ConversationChannel
    metadata: dict
    status: str
    created: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    updated: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )


@dataclass_json
@dataclass(frozen=True)
class Attachment:
    type: AttachmentType
    file_name: str


@dataclass(frozen=True)
class WebhookConversation:
    """
    Details of the conversation the event relates to.
    """

    conversation_id: str = field(metadata=config(field_name="id"))
    """
    The conversation's assigned identifier.
    """

    customer_id: str
    """
    The customer's assigned identifier.
    """

    metadata: Any
    """
    Arbitrary metadata attached to the conversation.
    """


@dataclass_json
@dataclass(frozen=True)
class AgentMessageEvent:
    """
    An event that represents a message from the agent.
    """

    conversation: WebhookConversation
    """
    Details of the conversation the event relates to.
    """

    body: str
    """
    Text of the agent's message.
    """

    total: Optional[int] = 0
    """
    total identifies the number of agent messages that have been
	produced in the current turn.
    """

    sequence: Optional[int] = 0
    """
    sequence identifies which agent message this is in the current turn.
    """

    intent: Optional[str] = None
    """
    intent is the most recent intent that was classified from the customer's
    conversation, if any.
    """


@dataclass_json
@dataclass(frozen=True)
class ConversationHandOffEvent:
    conversation: WebhookConversation
    """
    Details of the conversation the event relates to.
    """
    reason_code: str
    """
    reason_code is the code that describes why the agent wants to hand off this
    conversation.
    """
    
    reason: str
    """
    reason is a human-legible description of the Reason code.
    """

    note: Optional[str] = None
    """
    Note is a human-legible summary of the conversation so far, for a smooth hand-off.
    """

    intent: Optional[str] = None
    """
    Intent is the most recent intent that was classified from the customer's conversation, if any.
    """

    target: Optional[str] = None
    """
    Target defines where the agent wants to hand this conversation to.
    """


@dataclass_json
@dataclass(frozen=True)
class ConversationFinishedEvent:
    conversation: WebhookConversation
    """
    Details of the conversation the event relates to.
    """


@dataclass_json
@dataclass(frozen=True)
class ActionExecuteEvent:
    conversation: WebhookConversation
    """
    Details of the conversation the event relates to.
    """

    action: str
    """
    The action's given identifier.
    """

    params: Dict[str, Any]
    """
    Parameters the agent has generated for this action.
    """


@dataclass_json
@dataclass(frozen=True)
class WebhookEvent:
    event_id: str = field(metadata=config(field_name="id"))
    """
    Unique identifier for this event.
    """

    event_type: str = field(metadata=config(field_name="type"))
    """
    Type of event (see: https://api-docs.gradient-labs.ai/#webhooks).
    """

    sequence_number: int
    """
    Sequential index of this event within the conversation (see: https://api-docs.gradient-labs.ai/#sequence-numbers).
    """

    timestamp: datetime = field(
        metadata=config(
            decoder=datetime.fromisoformat, mm_field=fields.DateTime(format="iso")
        )
    )
    """
    Time at which this event was generated.
    """

    data: Any
    """
    Event data
    """
