"""Corvic table specific errors."""

from corvic import result


class OpParseError(result.Error):
    """Raised when parsing an op encounters a problem."""
