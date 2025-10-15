from enum import StrEnum

from openmodule.models.base import OpenModuleModel, CostEntryData, Base64Payload


class ValidateRequestTicketType(StrEnum):
    qr = "qr"
    nfc = "nfc"


class ValidateResponseState(StrEnum):
    ok = "ok"
    not_applicable = "not_applicable"


class ValidateResponseError(StrEnum):
    # the ticket is valid but it was already used once and cannot be used multiple times
    already_used = "already_used"

    # the ticket is invalid, e.g. the signature is incorrect
    invalid = "invalid"

    # the ticket is valid, but cannot be used for various reasons, please provide more
    # information in the `message` field in this case.
    excluded = "excluded"

    # is expired or cannot be used at this point in time
    expired = "expired"

    # an unknown error has occured while processing the ticket
    unknown_error = "unknown_error"


class ValidateRequest(OpenModuleModel):
    name: str
    session_id: str
    type: ValidateRequestTicketType
    payload: Base64Payload
    gate: str | None = None


class ValidateResponse(OpenModuleModel):
    state: ValidateResponseState
    error: ValidateResponseError | None = None
    cost_entries: list[CostEntryData] | None = None
    message: str | None = None
