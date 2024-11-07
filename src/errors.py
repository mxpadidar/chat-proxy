import json


class BaseError(Exception):
    def __init__(self, message: str, type: str) -> None:
        self.message = message
        self.type = type
        super().__init__(message)

    def json(self) -> str:
        return json.dumps(
            {"status": "error", "type": self.type, "message": self.message}
        )


class ValidationError(BaseError):
    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, "validation_error")


class MissingHeaderError(BaseError):
    def __init__(self, key: str) -> None:
        message = f"Header key not found: {key}"
        super().__init__(message, "missing_header")
