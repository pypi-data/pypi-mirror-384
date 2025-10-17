import os
import sys
import uuid
from datetime import datetime
import logging

from gradient_labs import (
    Client,
    ConversationChannel,
    ParticipantType,
    Attachment,
    AttachmentType,
    ResponseError,
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

client = Client(
    api_key=os.environ["GLABS_API_KEY"],
    base_url="http://localhost:4000",
)

conv = client.start_conversation(
    conversation_id=str(uuid.uuid4()),
    customer_id="snake",
    channel=ConversationChannel.WEB,
)

logging.info(f"✅ Conversation started: {conv.id}")

client.add_message(
    conversation_id=conv.id,
    message_id=str(uuid.uuid4()),
    body="Hello, how can we help you?",
    participant_type=ParticipantType.BOT,
    participant_id="bot",
)
logging.info("✅ Bot message added")

client.add_message(
    conversation_id=conv.id,
    message_id=str(uuid.uuid4()),
    body="Hello! Could I have a bank statement?",
    participant_type=ParticipantType.CUSTOMER,
    participant_id="user_123",
    created=datetime.now(),
)
logging.info("✅ Customer message added")

try:
    client.assign_conversation(
        conversation_id=conv.id,
        participant_type=ParticipantType.AI_AGENT,
    )
    logging.info("✅ Assigned to Gradient Labs")
except ResponseError as exc:
    if exc.status_code == 400:
        logging.info("✅ Cannot assign to Gradient Labs without a webhook")


client.assign_conversation(
    conversation_id=conv.id,
    participant_type=ParticipantType.HUMAN_AGENT,
)
logging.info("✅ Assigned to a human agent")

client.add_message(
    conversation_id=conv.id,
    message_id=str(uuid.uuid4()),
    body="Sure, here it is!",
    participant_type=ParticipantType.HUMAN_AGENT,
    participant_id="agent_123",
    attachments=[
        Attachment(
            type=AttachmentType.FILE,
            file_name="bank_statement.pdf",
        )
    ],
)
logging.info("✅ Human agent message added")

client.add_resource(
    conversation_id=conv.id,
    name="account-details",
    data={
        "sort_code": "123456",
        "account_type": "personal",
    },
)
logging.info("✅ Resource added")

client.end_conversation(conversation_id=conv.id)
logging.info(f"✅ Conversation closed: {conv.id}")

conv = client.read_conversation(conversation_id=conv.id)
logging.info(f"✅ Conversation status is: {conv.status}")
