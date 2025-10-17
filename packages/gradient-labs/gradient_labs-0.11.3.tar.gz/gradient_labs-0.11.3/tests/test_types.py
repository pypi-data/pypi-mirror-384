import pytest
from datetime import datetime

from gradient_labs.conversation import Conversation


@pytest.fixture
def now() -> str:
    return datetime.now()


def test_conversation(now):
    body = {
        "id": "id-1234",
        "customer_id": "cust-456",
        "channel": "email",
        "created": now.isoformat(),
        "updated": now.isoformat(),
        "metadata": {
            "user_type": "premium",
        },
        "status": "open",
    }
    got = Conversation.from_dict(body)
    want = Conversation(
        id="id-1234",
        customer_id="cust-456",
        channel="email",
        created=now,
        updated=now,
        metadata={
            "user_type": "premium",
        },
        status="open",
    )
    assert want == got
