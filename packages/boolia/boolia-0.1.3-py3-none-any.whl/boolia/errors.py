class MissingVariableError(NameError):
    """Raised when a required variable/path is missing."""

    def __init__(self, parts):
        super().__init__(f"Missing variable/path: {'.'.join(parts)}")
        self.parts = parts


class RulebookError(Exception):
    """Base class for rulebook serialization errors."""


class RulebookSerializationError(RulebookError):
    """Raised when serialization fails (e.g. missing dependencies)."""


class RulebookValidationError(RulebookError):
    """Raised when a serialized payload does not match the expected schema."""


class RulebookVersionError(RulebookError):
    """Raised when a serialized payload uses an unsupported schema version."""
