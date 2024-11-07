import json
from dataclasses import dataclass, field

from enums import MessageType
from errors import MissingHeaderError, ValidationError


@dataclass
class Message:
    type: MessageType
    body: dict = field(default_factory=dict)  # user, message, recipient, etc.
    headers: dict = field(default_factory=dict)  # proxy, credentials, etc.

    @staticmethod
    def from_json(json_str: str) -> "Message":
        data: dict = json.loads(json_str)
        try:
            type = MessageType.from_str(data["type"])
            body = data.get("body", {})
            headers = data.get("headers", {})
        except ValidationError as e:
            raise e

        return Message(type=type, body=body, headers=headers)

    def to_json(self) -> str:
        return json.dumps({"type": self.type.value, "body": self.body, "headers": self.headers})

    @property
    def proxy(self) -> str:
        try:
            return self.headers["proxy"]
        except KeyError:
            raise MissingHeaderError("proxy")

    @proxy.setter
    def proxy(self, value: str) -> None:
        self.headers["proxy"] = value

    @property
    def user(self) -> str:
        try:
            return self.body["user"]
        except KeyError:
            raise ValidationError("user")

    @property
    def message(self) -> str:
        try:
            return self.body["message"]
        except KeyError:
            raise ValidationError("Message key not found")

    @property
    def recipient(self) -> str:
        try:
            return self.body["recipient"]
        except KeyError:
            raise ValidationError("Recipient key not found")
