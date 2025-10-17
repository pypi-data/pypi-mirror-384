import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Optional
from pytz import UTC
from .errors import SignatureVerificationError
from .conversation import *


@dataclass(frozen=True)
class WebhookSignature:
    valid: bool
    """
    Is the signature header well-formed and signed with a known key?

    Note: you must also check `timestamp` to prevent replay attacks.
    """

    timestamp: Optional[datetime]
    """
    When was the signature generated? Use this to prevent replay attacks.
    """


class Webhook:
    SCHEME = "v1"
    LEEWAY = timedelta(minutes=5)

    @classmethod
    def parse_event(
        cls,
        *,
        payload: str,
        signature_header: str,
        signing_key: str,
    ) -> WebhookEvent:
        """
        Parse the webhook request body and verify the signature header.
        Raises SignatureVerificationError if the signature is invalid.
        """

        sig = cls.parse_signature_header(
            payload=payload,
            header=signature_header,
            signing_key=signing_key,
        )
        if not sig.valid:
            raise SignatureVerificationError("invalid signature")
        if abs(UTC.localize(datetime.now()) - sig.timestamp) > cls.LEEWAY:
            raise SignatureVerificationError("expired signature")

        data = json.loads(payload)
        if data["type"] == "agent.message":
            data["data"] = AgentMessageEvent.from_dict(data["data"])
        elif data["type"] == "conversation.hand_off":
            data["data"] = ConversationHandOffEvent.from_dict(data["data"])
        elif data["type"] == "conversation.finished":
            data["data"] = ConversationFinishedEvent.from_dict(data["data"])
        elif data["type"] == "action.execute":
            data["data"] = ActionExecuteEvent.from_dict(data["data"])
        return WebhookEvent.from_dict(data)

    @classmethod
    def parse_signature_header(
        cls,
        *,
        payload: str,
        header: str,
        signing_key: str,
    ) -> WebhookSignature:
        try:
            timestamp, signatures = cls._get_timestamp_and_signatures(
                header, cls.SCHEME
            )
        except:
            return WebhookSignature(valid=False, timestamp=None)

        signed_payload = "%d.%s" % (timestamp, payload)
        expected_sig = cls._compute_signature(signed_payload, signing_key)

        valid = any(hmac.compare_digest(expected_sig, s) for s in signatures)
        return WebhookSignature(
            timestamp=UTC.localize(datetime.fromtimestamp(timestamp)),
            valid=valid,
        )

    @staticmethod
    def _get_timestamp_and_signatures(header, scheme):
        list_items = [i.split("=", 2) for i in header.split(",")]
        timestamp = int([i[1] for i in list_items if i[0] == "t"][0])
        signatures = [i[1] for i in list_items if i[0] == scheme]
        return timestamp, signatures

    @staticmethod
    def _compute_signature(payload, secret):
        mac = hmac.new(
            secret.encode("utf-8"),
            msg=payload.encode("utf-8"),
            digestmod=sha256,
        )
        return mac.hexdigest()

    @classmethod
    def generate_signature_header(
        cls,
        *,
        payload: str,
        signing_key: str,
        ts: Optional[datetime] = None,
    ) -> str:
        if ts is None:
            ts = UTC.localize(datetime.now())
        ts_unix = ts.timestamp()
        data = "%d.%s" % (ts_unix, payload)
        sig = cls._compute_signature(data, signing_key)
        return "t=%d,v1=%s" % (ts_unix, sig)
