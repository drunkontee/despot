from typing import Any, ClassVar


class DespotException(Exception):
    default_message: ClassVar[str]

    def __init__(self, msg: str | None = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(msg or self.default_message, *args, **kwargs)


class StreamError(DespotException):
    default_message = "Failed to open stream"


class FilenameTemplateError(DespotException):
    default_message = "Invalid filename template"


class ContentUnavailableError(StreamError):
    default_message = "Track is not available to you"
