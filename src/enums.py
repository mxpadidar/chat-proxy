from enum import StrEnum, auto
from typing import Type, TypeVar

from errors import ValidationError

T = TypeVar("T", bound="MessageType")


class MessageType(StrEnum):
    REGISTER_PROXY = auto()
    USER_REGISTER = auto()
    CHAT = auto()
    SERVER_RESPONSE = auto()
    SERVER_ERROR = auto()

    @classmethod
    def from_str(cls: Type[T], value: str) -> T:
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValidationError
