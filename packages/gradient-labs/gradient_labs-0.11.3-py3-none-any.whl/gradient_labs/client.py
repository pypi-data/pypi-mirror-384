from typing import Any, Optional, List

from ._article_delete import delete_article
from ._article_set_status import set_article_usage_status, SetArticleUsageStatusParams
from ._article_topic_upsert import upsert_article_topic, ArticleTopicUpsertParams
from ._article_upsert import upsert_article, UpsertArticleParams

from .conversation import Conversation
from ._conversation_add_message import add_message, AddMessageParams, Message
from ._conversation_add_resource import add_resource
from ._conversation_assign import assign_conversation, AssignmentParams
from ._conversation_cancel import cancel_conversation, CancelParams
from ._conversation_event import add_conversation_event, EventParams
from ._conversation_finish import finish_conversation, FinishParams
from ._conversation_rate import rate_conversation, RatingParams
from ._conversation_resume import resume_conversation, ResumeParams
from ._conversation_read import read_conversation, ReadParams
from ._conversation_start import start_conversation, StartConversationParams

from ._handoff_target_upsert import upsert_hand_off_target, UpsertHandOffTargetParams
from ._handoff_targets import list_handoff_targets, HandOffTargets
from ._handoff_target_delete import delete_hand_off_target, DeleteHandOffTargetParams
from ._handoff_target_set_default import (
    set_default_hand_off_target,
    SetDefaultHandOffTargetParams,
)

from .procedure import Procedure
from ._procedure_read import read_procedure
from ._procedure_list import list_procedures, ProcedureListParams, ProcedureListResponse
from ._procedure_set_limit import set_procedure_limit, ProcedureLimitParams

from ._tool_create import create_tool
from ._tool_delete import delete_tool
from ._tool_execute import execute_tool, ToolExecuteParams, ToolExecuteResult
from ._tool_list import list_tools
from ._tool_read import read_tool
from ._tool_update import update_tool

from ._http_client import HttpClient, API_BASE_URL
from .tool import *
from .webhook import Webhook, WebhookEvent


class Client:
    """Client is the client for the Gradient Labs
    public api. For full details, please refer to the online docs:

    https://api-docs.gradient-labs.ai/
    """

    def __init__(
        self,
        *,
        api_key: str,
        signing_key: Optional[str] = None,
        base_url: Optional[str] = API_BASE_URL,
        timeout: Optional[int] = None,
    ):
        self.http_client = HttpClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self.signing_key = signing_key

    def delete_article(self, *, id: str) -> None:
        """delete_article marks an article as deleted. Copies of the article are kept
        in case they are needed to render citations."""
        delete_article(
            client=self.http_client,
            id=id,
        )

    def set_article_usage_status(
        self, *, id: str, params: SetArticleUsageStatusParams
    ) -> None:
        """set_article_usage_status updates an article's usage status. Use this to
        make it (un)available for use by the AI agent."""
        set_article_usage_status(
            client=self.http_client,
            id=id,
            params=params,
        )

    def upsert_article_topic(self, *, params: ArticleTopicUpsertParams) -> None:
        """upsert_article_topic inserts or updates a help article topic"""
        upsert_article_topic(
            client=self.http_client,
            params=params,
        )

    def upsert_article(self, *, params: UpsertArticleParams) -> None:
        """upsert_article inserts or updates a help article"""
        upsert_article(
            client=self.http_client,
            params=params,
        )

    def assign_conversation(
        self,
        *,
        conversation_id: str,
        params: AssignmentParams,
    ) -> None:
        """Assigns a conversation to the given participant."""
        assign_conversation(
            client=self.http_client,
            conversation_id=conversation_id,
            params=params,
        )

    def cancel_conversation(
        self, *, conversation_id: str, params: CancelParams
    ) -> None:
        """cancel_conversation cancels the conversation.

        This is intended for cases where the conversation is being explicitly cancelled or terminated.
        Use finish_conversation() when the conversation is has reached a natural 'end' state, such as it being
        resolved or closed due to inactivity."""
        cancel_conversation(
            client=self.http_client,
            conversation_id=conversation_id,
            params=params,
        )

    def add_conversation_event(
        self, *, conversation_id: str, params: EventParams
    ) -> None:
        """add_conversation_event records an event, such as the customer started typing."""
        add_conversation_event(
            client=self.http_client,
            conversation_id=conversation_id,
            params=params,
        )

    def finish_conversation(
        self,
        *,
        conversation_id: str,
        params: FinishParams,
    ) -> None:
        """finish_conversation finishes a conversation.

        A conversation finishes when it has come to its natural conclusion. This could be because
        the customer's query has been resolved, a human agent or other automation has closed the chat,
        or because the chat is being closed due to inactivity."""
        finish_conversation(
            client=self.http_client,
            conversation_id=conversation_id,
            params=params,
        )

    def rate_conversation(self, *, conversation_id: str, params: RatingParams) -> None:
        """rate_conversation submits a customer (CSAT) rating for a conversation."""
        rate_conversation(
            client=self.http_client,
            conversation_id=conversation_id,
            params=params,
        )

    def resume_conversation(self, *, conversation_id: str, params: ResumeParams) -> None:
        """resume_conversation re-opens a conversation that was previously finished."""
        resume_conversation(
            client=self.http_client,
            conversation_id=conversation_id,
            params=params,
        )

    def read_conversation(
        self, *, conversation_id: str, params: ReadParams
    ) -> Conversation:
        """Retrieves the conversation"""
        return read_conversation(
            client=self.http_client,
            conversation_id=conversation_id,
            params=params,
        )

    def start_conversation(
        self,
        *,
        params: StartConversationParams,
    ) -> Conversation:
        """Starts a conversation."""
        return start_conversation(
            client=self.http_client,
            params=params,
        )

    def add_message(
        self,
        *,
        conversation_id: str,
        params: AddMessageParams,
    ) -> Message:
        """Adds a message to a conversation."""
        return add_message(
            client=self.http_client,
            conversation_id=conversation_id,
            params=params,
        )

    def add_resource(
        self,
        *,
        conversation_id: str,
        name: str,
        data: Any,
    ) -> None:
        """add_resource adds (or updates) a resource to the conversation (e.g. the
        customer's order details) so the AI agent can handle customer-specific queries.

        A resource can be any JSON document, as long it is smaller than 1MB. There
        are no strict requirements on the format/structure of the document, but we
        recommend making attribute names as descriptive as possible.

        Over time, the AI agent will learn the structure of your resources - so while
        it's fine to add new attributes, you may want to consider using new resource
        names when removing attributes or changing the structure of your resources
        significantly.

        Resource names are case-insensitive and can be anything consisting of letters,
        numbers, or any of the following characters: _ - + =.

        Names should be descriptive handles that are the same for all conversations
        (e.g. "order-details" and "user-profile") not unique identifiers."""
        add_resource(
            client=self.http_client,
            conversation_id=conversation_id,
            name=name,
            resource=data,
        )

    def upsert_hand_off_target(self, *, params: UpsertHandOffTargetParams) -> None:
        """upsert_hand_off_target inserts or updates a hand-off target.

        Note: requires a `Management` API key."""
        upsert_hand_off_target(
            client=self.http_client,
            params=params,
        )

    def set_default_hand_off_target(
        self, *, params: SetDefaultHandOffTargetParams
    ) -> None:
        """set_default_hand_off_target sets the default hand-off target that the AI agent will
        use when handing off the conversation, if there is no specific target for that intent
        or procedure. This can be set by channel.

        Note: requires a `Management` API key."""
        set_default_hand_off_target(
            client=self.http_client,
            params=params,
        )

    def delete_hand_off_target(self, *, params: DeleteHandOffTargetParams) -> None:
        """delete_hand_off_target deletes a hand-off target. This will fail if the hand off target
        is in use - either in a procedure, or in an intent.

        Note: requires a `Management` API key."""
        delete_hand_off_target(
            client=self.http_client,
            params=params,
        )

    def list_handoff_targets(self) -> HandOffTargets:
        """list_handoff_targets returns all of your hand off targets.

        Note: requires a `Management` API key."""
        return list_handoff_targets(client=self.http_client)

    def read_procedure(self, *, procedure_id: str) -> Procedure:
        """read_procedure reads a procedure.

        Note: requires a `Management` API key."""
        return read_procedure(
            client=self.http_client,
            procedure_id=procedure_id,
        )

    def list_procedures(self, *, params: ProcedureListParams) -> ProcedureListResponse:
        """list_procedures lists procedures.

        Note: requires a `Management` API key."""
        return list_procedures(
            client=self.http_client,
            params=params,
        )

    def set_procedure_limit(
        self, *, procedure_id: str, params: ProcedureLimitParams
    ) -> Procedure:
        """set_procedure_limit updates the daily usage limit of a procedure.

        Note: requires a `Management` API key."""
        return set_procedure_limit(
            client=self.http_client,
            procedure_id=procedure_id,
            params=params,
        )

    def create_tool(self, *, tool: Tool) -> Tool:
        """create_tool creates a new tool.

        Note: requires a `Management` API key."""
        return create_tool(
            client=self.http_client,
            params=tool,
        )

    def delete_tool(self, *, tool_id: str):
        """delete_tool deletes a tool. Note: will not allow to delete a tool used in an active procedure.

        Note: requires a `Management` API key."""
        delete_tool(
            client=self.http_client,
            tool_id=tool_id,
        )

    def execute_tool(self, *, params: ToolExecuteParams) -> ToolExecuteResult:
        """execute_tool executes a tool.

        Note: requires a `Management` API key."""
        return execute_tool(
            client=self.http_client,
            params=params,
        )

    def read_tool(self, *, tool_id: str) -> Tool:
        """read_tool retrieves a new tool.

        Note: requires a `Management` API key."""
        return read_tool(
            client=self.http_client,
            tool_id=tool_id,
        )

    def list_tools(self) -> List[Tool]:
        """list_tools lists all tools.

        Note: requires a `Management` API key."""
        return list_tools(
            client=self.http_client,
        )

    def update_tool(self, *, params: ToolUpdateParams) -> Tool:
        """update_tool updates an existing tool. It allows callers to convert mock tools
        into real tools, but not the other way around.

        Note: requires a `Management` API key."""
        return update_tool(
            client=self.http_client,
            params=params,
        )

    def parse_webhook(self, payload: str, signature_header: str) -> WebhookEvent:
        """parse_webhook parses a webhook event."""
        return Webhook.parse_event(
            payload=payload,
            signature_header=signature_header,
            signing_key=self.signing_key,
        )
