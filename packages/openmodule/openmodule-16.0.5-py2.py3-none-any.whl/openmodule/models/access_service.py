from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from openmodule.models.base import OpenModuleModel, Datetime
from openmodule.models.vehicle import Medium, LPRMedium, MakeModel
from openmodule.utils.misc_functions import utcnow


class AccessCategory(StrEnum):
    handauf = "handauf"                     # handauf qr codes
    whitelist = "whitelist"                 # whitelist or other access services giving unrestricted free access
    booked = "booked"                       # anything already paid for (e.g. reservations)
    permanent = "permanent"                 # anything without parking costs except two cases above
    shortterm = "shortterm"                 # accesses with parking costs
    unknown = "unknown"                     # no access at all (unregistered shortterm parker)
    # in bypass and only permitted garages, users entered via external system (bypass system, key, ...)
    # Not used by access services
    external = "external"


class AccessRequestVehicle(OpenModuleModel):
    """
    The AccessRequestVehicle Model, represents all data sent by the controller,
     each backend should implement its own version to avoid problems when unnecessary fields change
    """
    lpr: LPRMedium | None = None
    qr: Medium | None = None
    pin: Medium | None = None
    nfc: Medium | None = None
    make_model: MakeModel | None = None


class AccessCheckRequest(OpenModuleModel):
    """
    The AccessRequest Model
    """
    name: str                                                      # Name of the target Access Service
    gate: str | None = None                                        # None means any gate
    vehicle: AccessRequestVehicle                                  # vehicle data
    vehicle_id: str | None = None                                  # vehicle id, if known (for event linking)
    timestamp: Datetime = Field(default_factory=lambda: utcnow())  # check if access valid at this time


class AccessCheckRejectReason(StrEnum):  # see DEV-A-916
    wrong_gate = "wrong_gate"  # no valid at this gate
    wrong_time = "wrong_time"  # no valid at this time
    custom = "custom"  # some access service specific reason for rejection


class AccessCheckAccess(OpenModuleModel):
    id: str                                                 # id of the access
    group_id: str | None = None                             # id for group-passback, in Digimon Contract ID, optional for 3rd Party Backends
    group_limit: int | None = Field(default=None, ge=1)     # group_limit must be greater or equal 1
    customer_id: str | None = None                          # in Digimon Customer ID, optional for 3rd Party Backends
    car_id: str | None = None                               # in Digimon Customer Car ID, optional for 3rd Party Backends
    source: str                                             # Access Service providing the access
    access_infos: dict = {}                                 # Infos, which are added everywhere for later usage
    parksettings_id: str | None = None                      # None is no cost entries and access at any gate
    clearing: str | None = None                             # Clearing
    clearing_infos: dict | None = None                      # Infos, which are added everywhere for later usage when using clearing
    category: AccessCategory                                # category used for sorting and eventlog
    used_medium: Medium                                     # medium of the access
    access_data: dict                                       # complete access data, will be used only for display and debug purposes
    valid_from: Datetime | None = None                      # access is valid from this time. Only used for reservations
    valid_to: Datetime | None = None                        # access is valid until this time. Only used for reservations

    accepted: bool                                          # if access service decided access can enter
    reject_reason: AccessCheckRejectReason | None = None    # only if not accepted: reason for not accepted
    # additional infos shown in events if reject reason is "custom". Required if reject_reason == "custom"
    supplementary_infos: str | None = None

    @model_validator(mode="after")
    def root_validation(self) -> Self:
        # if category is handauf, medium_display_name must be set
        if self.category == AccessCategory.handauf and "medium_display_name" not in self.access_infos:
            raise ValueError("medium_display_name must be set if category is handauf")
        if self.category == AccessCategory.external:
            raise ValueError("category external is not allowed for accesses")
        if self.group_limit is not None and self.group_id is None:
            raise ValueError("group_limit must not be set without group_id")
        if self.category in [AccessCategory.shortterm, AccessCategory.unknown] \
                and self.group_limit is not None:
            raise ValueError("group_limit must not be set for shortterm and unknown accesses")
        if self.reject_reason is AccessCheckRejectReason.custom and self.supplementary_infos in ["", None]:
            raise ValueError("supplementary_infos must be set if reject_reason is custom")
        return self


class AccessCheckResponse(OpenModuleModel):
    success: bool
    accesses: list[AccessCheckAccess] = []  # list of all matched accesses (including already rejected ones)
