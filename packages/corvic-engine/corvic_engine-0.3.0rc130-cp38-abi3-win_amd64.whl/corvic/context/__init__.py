"""Per-request context variables.

Affect things like logging and the names of metrics.
"""

import contextvars
from dataclasses import dataclass

# These are sentinels used only in the Requester object below rather than actual org
# ids that our query middleware uses to make query instrumentation decisions
NOBODY_ORG_ID = "org-nobody"  # an org that owns nothing
SUPERUSER_ORG_ID = "org-superuser"  # an org that can see everything


@dataclass(frozen=True)
class Requester:
    """Info about the issuer of the request, populated by middleware."""

    org_id: str


_SERVICE_NAME: contextvars.ContextVar[str] = contextvars.ContextVar(
    "service_name", default="corvic"
)
_REQUESTER: contextvars.ContextVar[Requester | None] = contextvars.ContextVar(
    "requester_identity", default=None
)


def get_service_name() -> str:
    """Get current service name."""
    return _SERVICE_NAME.get()


def get_requester() -> Requester:
    """Get current requester."""
    requester = _REQUESTER.get()
    if requester is None:
        return Requester(org_id=NOBODY_ORG_ID)
    return requester


def reset_context(*, service_name: str):
    """Reset contextvars for a new request."""
    _ = _SERVICE_NAME.set(service_name)
    _ = _REQUESTER.set(Requester(org_id=NOBODY_ORG_ID))


def update_context(
    *, new_requester: Requester | None = None, new_service_name: str | None = None
):
    """Update selected contextvars for the current request."""
    if new_requester is not None:
        _ = _REQUESTER.set(new_requester)
    if new_service_name is not None:
        _ = _SERVICE_NAME.set(new_service_name)
