"""Errors specific to working with corvic models."""

from corvic import result


class InvalidOnAnonymousError(result.Error):
    """InvalidOnAnonymousError result Error.

    Raised when an operation cannot be done on an unregistered object.
    """
