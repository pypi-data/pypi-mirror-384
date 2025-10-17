"""Errors specific to communicating with the database."""

from sqlalchemy.exc import (
    DBAPIError,
    IntegrityError,
    InterfaceError,
    InternalError,
    NotSupportedError,
    OperationalError,
    ProgrammingError,
)

from corvic import result


class InvalidORMIdentifierError(result.InvalidArgumentError):
    """Raised when an identifier can't be translated to its orm equivalent."""


class RequestedObjectsForNobodyError(result.Error):
    """Raised when attempts are made to access database objects as the nobody org."""


class DeletedObjectError(result.Error):
    """DeletedObjectError result Error.

    Raised on invalid operations to objects which are soft deleted.
    """


def _map_sqlstate_error(
    err: DBAPIError,
) -> result.UnavailableError | result.AlreadyExistsError | None:
    """Classify DB errors based on SQL state.

    SQL state are stable, vendor specific error codes.
    Error codes referenced from https://www.postgresql.org/docs/current/errcodes-appendix.html
    """
    match getattr(err.orig, "sqlstate", ""):
        case "23505":  # unique violation
            return result.AlreadyExistsError.from_(err)
        case "40001":  # serialization failure
            return result.UnavailableError.from_(err)
        case _:
            return None


def _map_psycopg_error(
    err: DBAPIError,
) -> result.UnavailableError | result.AlreadyExistsError | None:
    try:
        import psycopg.errors  # noqa: PLC0415

        match err.orig:
            case psycopg.errors.SerializationFailure():
                return result.UnavailableError.from_(err)
            case psycopg.errors.UniqueViolation():
                return result.AlreadyExistsError.from_(err)
            case _:
                return None
    except ModuleNotFoundError:
        return None


def dbapi_error_to_result(
    err: DBAPIError,
) -> result.UnavailableError | result.InvalidArgumentError | result.AlreadyExistsError:
    sqlstate_err = _map_sqlstate_error(err)
    if sqlstate_err is not None:
        return sqlstate_err

    # based on https://docs.sqlalchemy.org/en/20/errors.html
    match err:
        case NotSupportedError():
            # raised in the unexpected case that we're doing something that the
            # database just doesn't support
            raise result.InternalError.from_(err) from err
        case OperationalError() | InterfaceError() | InternalError():
            # These are commonly things that are outside of our control that might
            # succeed on retry, e.g., connections being dropped
            return result.UnavailableError.from_(err)
        case IntegrityError() as err:
            if str(err.orig).startswith("UNIQUE constraint failed"):
                return result.AlreadyExistsError.from_(err)
            return result.InvalidArgumentError.from_(err)
        case ProgrammingError():
            if "could not serialize" in str(err):
                return result.UnavailableError.from_(err)
        case _:
            pass

    psycopg_err = _map_psycopg_error(err)
    if psycopg_err is not None:
        return psycopg_err

    return result.InvalidArgumentError.from_(err)
