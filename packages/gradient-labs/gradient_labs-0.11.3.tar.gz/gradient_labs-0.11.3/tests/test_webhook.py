from datetime import datetime, UTC
import pytest
from gradient_labs import *

WEBHOOK_KEY = "FNHtU3KZpxF3GfKSZXCNkUkPnVSPQygbdNMLHuibkPY="


class TestSignatureVerification:
    def test_valid(self):
        payload = '{"type":"foo.bar"}'
        header = "t=1699291314,v1=05b3faa3377aea763b67a528813bcd7357581fa3f75dd7bf870a83986c6a425f"

        signature = Webhook.parse_signature_header(
            payload=payload,
            header=header,
            signing_key=WEBHOOK_KEY,
        )
        assert signature.valid
        assert signature.timestamp == datetime(2023, 11, 6, 17, 21, 54, tzinfo=UTC)

    def test_bogus_header(self):
        payload = '{"type":"foo.bar"}'
        header = "bogus header"

        signature = Webhook.parse_signature_header(
            payload=payload,
            header=header,
            signing_key=WEBHOOK_KEY,
        )
        assert not signature.valid

    def test_wrong_key(self):
        payload = '{"type":"foo.bar"}'
        header = "t=1699291314,v1=05b3faa3377aea763b67a528813bcd7357581fa3f75dd7bf870a83986c6a425f"

        signature = Webhook.parse_signature_header(
            payload=payload,
            header=header,
            signing_key="bogus key",
        )
        assert not signature.valid


class TestParseEvent:
    def test_agent_message(self):
        payload = """
        {
          "id": "webhook_01he8rwyp4fn3v870d925kz2nf",
          "type": "agent.message",
          "sequence_number": 5,
          "timestamp": "2023-10-23T17:24:50.804952Z",
          "data": {
            "conversation": {
              "id": "conversation-1234",
              "customer_id": "user-1234",
              "metadata": {
                "chat_entrypoint": "home-page"
              }
            },
            "body": "Sure, I can help you set up your toaster oven!",
            "total": 1,
            "sequence": 1
          }
        }
        """

        signature_header = Webhook.generate_signature_header(
            payload=payload, signing_key=WEBHOOK_KEY
        )

        event = Webhook.parse_event(
            payload=payload,
            signature_header=signature_header,
            signing_key=WEBHOOK_KEY,
        )

        assert event == WebhookEvent(
            event_id="webhook_01he8rwyp4fn3v870d925kz2nf",
            event_type="agent.message",
            sequence_number=5,
            timestamp=datetime(2023, 10, 23, 17, 24, 50, 804952, tzinfo=UTC),
            data=AgentMessageEvent(
                conversation=WebhookConversation(
                    conversation_id="conversation-1234",
                    customer_id="user-1234",
                    metadata={
                        "chat_entrypoint": "home-page",
                    },
                ),
                body="Sure, I can help you set up your toaster oven!",
                total=1,
                sequence=1,
            ),
        )

    def test_bad_signature(self):
        payload = """
        {
          "id": "webhook_01he8rwyp4fn3v870d925kz2nf",
          "type": "agent.message",
          "sequence_number": 5,
          "timestamp": "2023-10-23T17:24:50.804952Z",
          "data": {
            "conversation": {
              "id": "conversation-1234",
              "customer_id": "user-1234",
              "metadata": {
                "chat_entrypoint": "home-page"
              }
            },
            "body": "Sure, I can help you set up your toaster oven!"
          }
        }
        """

        with pytest.raises(SignatureVerificationError):
            Webhook.parse_event(
                payload=payload,
                signature_header="bogus header",
                signing_key=WEBHOOK_KEY,
            )

    def test_replay_attack(self):
        payload = """
        {
          "id": "webhook_01he8rwyp4fn3v870d925kz2nf",
          "type": "agent.message",
          "sequence_number": 5,
          "timestamp": "2023-10-23T17:24:50.804952Z",
          "data": {
            "conversation": {
              "id": "conversation-1234",
              "customer_id": "user-1234",
              "metadata": {
                "chat_entrypoint": "home-page"
              }
            },
            "body": "Sure, I can help you set up your toaster oven!"
          }
        }
        """

        signature_header = Webhook.generate_signature_header(
            payload=payload,
            signing_key=WEBHOOK_KEY,
            ts=datetime.now() - timedelta(minutes=10),
        )

        with pytest.raises(SignatureVerificationError):
            Webhook.parse_event(
                payload=payload,
                signature_header=signature_header,
                signing_key=WEBHOOK_KEY,
            )

    def test_conversation_handoff(self):
        payload = """
        {
          "id": "webhook_01he8rwyp4fn3v870d925kz2nf",
          "type": "conversation.hand_off",
          "sequence_number": 5,
          "timestamp": "2023-10-23T17:24:50.804952Z",
          "data": {
            "conversation": {
              "id": "conversation-1234",
              "customer_id": "user-1234",
              "metadata": {
                "chat_entrypoint": "home-page"
              }
            },
            "reason": "The customer asked for this.",
            "reason_code": "customer-request"
          }
        }
        """

        signature_header = Webhook.generate_signature_header(
            payload=payload, signing_key=WEBHOOK_KEY
        )

        event = Webhook.parse_event(
            payload=payload,
            signature_header=signature_header,
            signing_key=WEBHOOK_KEY,
        )

        assert event == WebhookEvent(
            event_id="webhook_01he8rwyp4fn3v870d925kz2nf",
            event_type="conversation.hand_off",
            sequence_number=5,
            timestamp=datetime(2023, 10, 23, 17, 24, 50, 804952, tzinfo=UTC),
            data=ConversationHandOffEvent(
                conversation=WebhookConversation(
                    conversation_id="conversation-1234",
                    customer_id="user-1234",
                    metadata={
                        "chat_entrypoint": "home-page",
                    },
                ),
                reason="The customer asked for this.",
                reason_code="customer-request",
            ),
        )

    def test_conversation_finished(self):
        payload = """
        {
          "id": "webhook_01he8rwyp4fn3v870d925kz2nf",
          "type": "conversation.finished",
          "sequence_number": 5,
          "timestamp": "2023-10-23T17:24:50.804952Z",
          "data": {
            "conversation": {
              "id": "conversation-1234",
              "customer_id": "user-1234",
              "metadata": {
                "chat_entrypoint": "home-page"
              }
            }
          }
        }
        """

        signature_header = Webhook.generate_signature_header(
            payload=payload, signing_key=WEBHOOK_KEY
        )

        event = Webhook.parse_event(
            payload=payload,
            signature_header=signature_header,
            signing_key=WEBHOOK_KEY,
        )

        assert event == WebhookEvent(
            event_id="webhook_01he8rwyp4fn3v870d925kz2nf",
            event_type="conversation.finished",
            sequence_number=5,
            timestamp=datetime(2023, 10, 23, 17, 24, 50, 804952, tzinfo=UTC),
            data=ConversationFinishedEvent(
                conversation=WebhookConversation(
                    conversation_id="conversation-1234",
                    customer_id="user-1234",
                    metadata={
                        "chat_entrypoint": "home-page",
                    },
                ),
            ),
        )

    def test_action_execute(self):
        payload = """
        {
          "id": "webhook_01he8rwyp4fn3v870d925kz2nf",
          "type": "action.execute",
          "sequence_number": 5,
          "timestamp": "2023-10-23T17:24:50.804952Z",
          "data": {
            "conversation": {
              "id": "conversation-1234",
              "customer_id": "user-1234",
              "metadata": {
                "chat_entrypoint": "home-page"
              }
            },
            "action": "random-dog-fact",
            "params": {
              "breed": "Golden Retriever"
            }
          }
        }
        """

        signature_header = Webhook.generate_signature_header(
            payload=payload, signing_key=WEBHOOK_KEY
        )

        event = Webhook.parse_event(
            payload=payload,
            signature_header=signature_header,
            signing_key=WEBHOOK_KEY,
        )

        assert event == WebhookEvent(
            event_id="webhook_01he8rwyp4fn3v870d925kz2nf",
            event_type="action.execute",
            sequence_number=5,
            timestamp=datetime(2023, 10, 23, 17, 24, 50, 804952, tzinfo=UTC),
            data=ActionExecuteEvent(
                conversation=WebhookConversation(
                    conversation_id="conversation-1234",
                    customer_id="user-1234",
                    metadata={
                        "chat_entrypoint": "home-page",
                    },
                ),
                action="random-dog-fact",
                params={
                    "breed": "Golden Retriever",
                },
            ),
        )
