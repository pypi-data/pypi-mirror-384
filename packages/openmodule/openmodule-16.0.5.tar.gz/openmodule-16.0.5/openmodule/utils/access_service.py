import dataclasses
import logging

from settings_models.settings.common import GateType

from openmodule import sentry
from openmodule.config import settings
from openmodule.models.access_service import \
    AccessCheckRequest, AccessCheckResponse, AccessCheckAccess, AccessCheckRejectReason, AccessCategory
from openmodule.models.vehicle import LPRMedium
from openmodule.rpc.server import RPCServer
from openmodule.utils.charset import CharsetConverter, legacy_lpr_charset
from openmodule.utils.matching import PlateYamlSelector, MatchingConfig
from openmodule.utils.settings import SettingsProvider


class AccessService:
    """
    AccessService template class
    provides basic functionality used for backups
    * subscribes to AccessServiceMessages and automatically registers AccessService
    * provides method for the AccessService / auth rpc with the check_access_service_access method

    """

    def __init__(self):
        self.log = logging.getLogger()

    def register_rpcs(self, rpc_server: RPCServer):
        rpc_server.add_filter(self._access_service_filter, "access_service", "auth")
        rpc_server.register_handler("access_service", "auth", request_class=AccessCheckRequest,
                                    response_class=AccessCheckResponse, handler=self.rpc_check_access)

    def _access_service_filter(self, request, message, handler) -> bool:
        access_service = request.name
        if not access_service:
            return False
        return settings.NAME == access_service

    def rpc_check_access(self, request: AccessCheckRequest, _) -> AccessCheckResponse:
        """
        Check if the user has access at the given gate at the given time according to DEV-A-916
        """

        raise NotImplementedError()


# util functions for an access service
log = logging.getLogger("AccessServiceUtils")
lpr_search_converter = CharsetConverter(legacy_lpr_charset)


@dataclasses.dataclass
class LPRKnownAccess:
    id: str
    lpr_id: str
    lpr_country: str
    matching_scheme: str | None = None
    matching_version: int | None = None


def get_lpr_id_search(lpr_id: str) -> str:
    """This function converts the given lpr_id to the search format"""
    return lpr_search_converter.clean(lpr_id)


def deduplicate_accesses(accesses: list[AccessCheckAccess]) -> list[AccessCheckAccess]:
    """This function removes duplicates from the given list of accesses. It keeps the first occurrence of each id."""
    res = []
    ids = set()
    for access in accesses:
        if access.id not in ids:
            res.append(access)
            ids.add(access.id)
    return res


def _find_lpr_accesses_ed0(medium: LPRMedium, accesses: list[LPRKnownAccess], matching_config: MatchingConfig) \
        -> list[LPRKnownAccess]:
    session_plate_db = {}
    plates = PlateYamlSelector.from_config(matching_config)
    for access in accesses:
        plates.insert_into_db_and_create_record(session_plate_db, access.lpr_id, access.lpr_country,
                                                access.matching_scheme or matching_config.default_scheme,
                                                access.matching_version if access.matching_version is not None
                                                else matching_config.default_version,
                                                access_id=access.id)
    to_match = plates.create_plate_for_matching(medium.id, medium.country.code, medium.confidence,
                                                medium.country.confidence, medium.alternatives)
    matches = plates.match_plate(to_match, session_plate_db,
                                 use_alternatives=matching_config.use_alternatives, max_ed=0,
                                 return_only_best=False)
    match_access_ids = sum([[o["access_id"] for o in eds] for eds in matches], [])
    return [access for access in accesses if access.id in match_access_ids]


@sentry.trace
def find_lpr_accesses(medium: LPRMedium, accesses: list[LPRKnownAccess], matching_config: MatchingConfig) \
        -> list[LPRKnownAccess]:
    """This functions tries to match the given LPR medium against a database of known accesses. It returns a list of
    all accesses that match the given medium. The matching is done according to the given matching_config"""
    if matching_config.edit_distance > 0:
        # we currently do not support matching accesses with edit distance
        # you can find the previous implementation, that supports edit distance here:
        # https://gitlab.com/arivo-public/device-python/openmodule/-/blob/cd02b94516c65c003bdf16417b74b40df3e83fa7/openmodule/utils/access_service.py#L278
        assert False, "You must not use edit distance to match accesses"
    else:
        matched = _find_lpr_accesses_ed0(medium, accesses, matching_config)
    return matched


@sentry.trace
def check_accesses_valid_at_gate(accesses: list[AccessCheckAccess], gate: str, settings: SettingsProvider):
    """This functions checks if the given accesses are valid at the given gate and sets the accepted flag and
    reject_reason accordingly"""
    gates = settings.get("common/gates")
    parking_areas = settings.get("common/parking_areas2")
    parksettings = settings.get("common/parksettings2")

    not_found_parksettings = []
    if gates.get(gate) and gates.get(gate).type == GateType.door:
        return  # no check necessary for doors

    for access in accesses:
        if access.accepted is False:
            continue  # already rejected
        parksetting = parksettings.get(access.parksettings_id)  # same behavior for parksetting None and not found
        if parksetting is None and access.parksettings_id is not None:
            not_found_parksettings.append(access.parksettings_id)

        if parksetting is None and access.category in [AccessCategory.shortterm, AccessCategory.unknown]:
            # treat like unknown shortterm parker -> check if gate is a shortterm gate
            if all(gate not in pa.shortterm_gates for pa in parking_areas.values()):
                access.accepted = False
                access.reject_reason = AccessCheckRejectReason.wrong_gate
        elif parksetting is None:
            pass  # no check necessary because access on all gates
        else:
            if access.category == AccessCategory.unknown:
                log.error("Parksetting not None for access of category unknown. This is an invalid access")
            elif access.category == AccessCategory.shortterm:
                log.error("Parksetting not None for access of category shortterm. This is an invalid access")
            # only check if parksetting_id is not None (None means any gate is ok)
            if gate not in parksetting.gates:
                access.accepted = False
                access.reject_reason = AccessCheckRejectReason.wrong_gate
    if not_found_parksettings:
        log.warning(f"Some parksettings set in access were not found in settings: {not_found_parksettings}")
