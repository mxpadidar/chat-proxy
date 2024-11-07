import json

import pytest

from enums import MessageType
from models import Message, MissingHeaderError, ValidationError


@pytest.fixture
def message_data() -> dict:
    return {
        "type": MessageType.CHAT,
        "body": {"user": "test", "message": "hello", "recipient": "user2"},
        "headers": {"proxy": "ws://localhost:8000"},
    }


def test_message_from_json(message_data: dict) -> None:
    msg = Message(**message_data)

    assert msg.type == MessageType.CHAT
    assert msg.body == message_data["body"]
    assert msg.headers == message_data["headers"]


def test_message_from_json_invalid_type(message_data: dict) -> None:
    message_data["type"] = "invalid"
    with pytest.raises(ValidationError):
        Message.from_json(json.dumps(message_data))


def test_message_to_json(message_data: dict) -> None:
    msg = Message(**message_data)
    msg_json = msg.to_json()

    msg_from_json = Message.from_json(msg_json)

    assert msg_from_json.type == msg.type
    assert msg_from_json.body == msg.body
    assert msg_from_json.headers == msg.headers


def test_missing_proxy_header(message_data: dict) -> None:
    del message_data["headers"]["proxy"]
    msg = Message(**message_data)
    with pytest.raises(MissingHeaderError):
        msg.proxy


def test_missing_user_body(message_data: dict) -> None:
    del message_data["body"]["user"]
    msg = Message(**message_data)
    with pytest.raises(ValidationError):
        msg.user


def test_missing_message_body(message_data: dict) -> None:
    del message_data["body"]["message"]
    msg = Message(**message_data)
    with pytest.raises(ValidationError):
        msg.message


def test_missing_recipient_body(message_data: dict) -> None:
    del message_data["body"]["recipient"]
    msg = Message(**message_data)
    with pytest.raises(ValidationError):
        msg.recipient
