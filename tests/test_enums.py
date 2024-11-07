import pytest

from enums import MessageType
from errors import ValidationError


def test_message_type_from_str_success() -> None:
    t = MessageType.from_str("registration")
    assert t == MessageType.USER_REGISTER
    assert t.value == "registration"


def test_message_type_from_str_invalid() -> None:

    with pytest.raises(ValidationError):
        MessageType.from_str("invalid")
