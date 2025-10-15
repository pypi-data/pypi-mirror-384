import os
import re
import uuid
from datetime import datetime
from typing import Optional
from unittest import TestCase

from settings_models.settings.common import Gate, GateType, ParkingArea, ShorttermLimitType, Parksetting
from sqlalchemy import String, event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from openmodule.config import settings
from openmodule.database.custom_types import JSONEncodedDict
from openmodule.database.database import Database
from openmodule.models.access_service import AccessCheckRequest, AccessCheckAccess, AccessCategory, \
    AccessCheckResponse, AccessCheckRejectReason
from openmodule.models.vehicle import LPRMedium, LPRCountry, Medium, QRMedium, MediumType
from openmodule.utils.access_service import AccessService, check_accesses_valid_at_gate, deduplicate_accesses, \
    get_lpr_id_search, LPRKnownAccess, find_lpr_accesses
from openmodule.utils.kv_store import KVStore, KVEntry
from openmodule.utils.matching import MatchingConfig
from openmodule_test.core import OpenModuleCoreTestMixin
from openmodule_test.database import SQLiteTestMixin
from openmodule_test.settings import SettingsMocker


def check_accesses_valid_at_time(accesses: list[AccessCheckAccess], time: datetime):
    """This functions checks if the given accesses are valid at the given time (e.g. request.timestamp) and sets
    the accepted flag and reject_reason accordingly"""
    for access in accesses:
        start = access.access_data.get("access_start") or datetime.min
        end = access.access_data.get("access_end") or datetime.max
        if not start <= time <= end:
            access.accepted = False
            access.reject_reason = AccessCheckRejectReason.wrong_time


class Base(DeclarativeBase):
    pass


class TestAccessModelBase(Base, KVEntry):
    __test__ = False
    __tablename__ = "test_access_model"

    # the KVEntry uses the field `key` as primary key, but we prefer our normal primary key 'id'
    @hybrid_property
    def id(self):
        return self.key

    @id.setter
    def id(self, value):
        self.key = value

    # ids for open session service
    customer_id: Mapped[Optional[str]]  # id used by open session service (customer id)
    car_id: Mapped[Optional[str]]  # id used by open session service (customer car id)
    group_id: Mapped[Optional[str]]  # id by open session service (contract id)

    parksettings_id: Mapped[Optional[str]]  # None is allowed for simplicity as only gates are necessary

    access_infos: Mapped[Optional[dict]] = mapped_column(JSONEncodedDict,
                                                         nullable=True)  # infos attached to all messages, null is empty dict

    # lpr with matching config
    lpr_id: Mapped[Optional[str]]
    lpr_id_search: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    lpr_country: Mapped[Optional[str]]
    matching_scheme: Mapped[Optional[str]]
    matching_version: Mapped[Optional[int]]

    # other media
    qr_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    regex: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)

    @classmethod
    def parse_value(cls, value: dict) -> list['TestAccessModelBase']:
        return [cls(**value)]


# this is just a convenience method that patches lpr_id_search,
# so that I don't need to set the lpr_id_search explicit on model creation
@event.listens_for(TestAccessModelBase, "before_update", propagate=True)
@event.listens_for(TestAccessModelBase, "before_insert", propagate=True)
def before_insert_and_update(_, __, target: TestAccessModelBase):
    if target.lpr_id:
        target.lpr_id_search = get_lpr_id_search(target.lpr_id)

    if (target.lpr_id is None) != (target.lpr_country is None):
        raise ValueError("field `lpr_country` must also be set iff `lpr_id` is set.")

    if not any([target.lpr_id, target.qr_id, target.regex]):
        raise ValueError("No id or regex set in access")


class AccessServiceExample(AccessService):
    def __init__(self, database: Database, settings_mocker: SettingsMocker,
                 matching_config: MatchingConfig | None = None):
        self.database = database
        self.settings = settings_mocker
        self.matching_config = matching_config or settings.YAML.matching_config
        super().__init__()

    @staticmethod
    def db_model_to_access(db_model: TestAccessModelBase, used_medium: Medium) -> AccessCheckAccess:
        common_data = dict(id=db_model.id, group_id=db_model.group_id, customer_id=db_model.customer_id,
                           car_id=db_model.car_id, access_infos=db_model.access_infos or {}, source="test",
                           parksettings_id=db_model.parksettings_id, category=AccessCategory.whitelist)
        access_data = dict(matching_scheme=db_model.matching_scheme, matching_version=db_model.matching_version)
        return AccessCheckAccess(access_data=access_data, used_medium=used_medium, accepted=True, **common_data)

    def find_lpr_accesses(self, medium: LPRMedium) -> list[AccessCheckAccess]:
        # we query our database with cleaned lpr, because cleaned lpr should be an index field, and it is faster
        # as transforming our whole database to the list of objects needed for the find_lpr_accesses() utils function
        plate_clean = get_lpr_id_search(medium.id)
        with self.database as db:
            res = db.query(TestAccessModelBase).filter(TestAccessModelBase.lpr_id_search == plate_clean).all()
            # we transform data into a dict for faster creation of AccessCheckAccess models with correct access id
            res = {r.id: r for r in res}
            known_accesses = [LPRKnownAccess(id=a.id, lpr_id=a.lpr_id, lpr_country=a.lpr_country,
                                             matching_scheme=a.matching_scheme, matching_version=a.matching_version)
                              for a in res.values()]
            matched = find_lpr_accesses(medium, known_accesses, self.matching_config)
            return [self.db_model_to_access(res[m.id], Medium(type=medium.type, id=m.id)) for m in matched]

    def find_regex_accesses(self, medium: LPRMedium) -> list[AccessCheckAccess]:
        with self.database as db:
            regexes = db.query(TestAccessModelBase).filter(TestAccessModelBase.regex.isnot(None)).all()
            return [self.db_model_to_access(access, Medium(type=MediumType.regex, id=access.regex))
                    for access in regexes if re.match(access.regex, medium.id)]

    def find_qr_accesses(self, medium: QRMedium) -> list[AccessCheckAccess]:
        with self.database as db:
            return [self.db_model_to_access(access, Medium(type=MediumType.qr, id=access.qr_id))
                    for access in db.query(TestAccessModelBase).filter(TestAccessModelBase.qr_id == medium.id).all()]

    def rpc_check_access(self, request: AccessCheckRequest, _) -> AccessCheckResponse:
        """
        Check if the user has access at the given gate at the given time according to DEV-A-916
        """
        self.log.debug(f"Check Access for {request.vehicle} at gate {request.gate}")

        accesses = []
        if request.vehicle.lpr:
            accesses += self.find_lpr_accesses(request.vehicle.lpr)
            accesses += self.find_regex_accesses(request.vehicle.lpr)
        if request.vehicle.qr:
            accesses += self.find_qr_accesses(request.vehicle.qr)

        accesses = deduplicate_accesses(accesses)

        # we mark the access invalid, if the access is currently not valid or the gate is incorrect for the access
        check_accesses_valid_at_time(accesses, request.timestamp)
        if request.gate:
            check_accesses_valid_at_gate(accesses, request.gate, self.settings)

        self.log.info(f"Found {len(accesses)} matching accesses "
                      f"where {len([a for a in accesses if a.accepted])} are valid")
        return AccessCheckResponse(success=True, accesses=accesses, readable_service_name=_("Test Access Service"))


class AccessKVStoreExample(KVStore):
    database_table = TestAccessModelBase


class WithDatabaseFunctionTest(SQLiteTestMixin, OpenModuleCoreTestMixin):
    alembic_path = "../tests/test_access_service_database"
    database_name = "access_service"
    settings = SettingsMocker({})
    matching_config = MatchingConfig(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            "resources/standard_schemes"))

    def setUp(self) -> None:
        super().setUp()
        self.access_service = AccessServiceExample(database=self.database, settings_mocker=self.settings,
                                                   matching_config=self.matching_config)
        self.kv_store = AccessKVStoreExample(db=self.database)

    def tearDown(self):
        super().tearDown()

    def test_find_lpr_accesses(self):
        with self.database as db:
            db.add(TestAccessModelBase(id="1", lpr_id="G ARIVO 1", lpr_country="A", matching_version=40))
            db.add(TestAccessModelBase(id="2", lpr_id="G ARIVO1", lpr_country="B", matching_version=30,
                                       access_infos={}))
            db.add(TestAccessModelBase(id="3", lpr_id="G:ARIVO1", lpr_country="CH", matching_version=20,
                                       access_infos={}))
            db.add(TestAccessModelBase(id="4", lpr_id="GARIVO1", lpr_country="D", matching_version=20,
                                       access_infos={}))
            db.add(TestAccessModelBase(id="5", lpr_id="GARIVO1", lpr_country="E",
                                       access_infos={}))  # is default 10
            db.add(TestAccessModelBase(id="6", lpr_id="GARIV01", lpr_country="F", matching_version=0,
                                       access_infos={}))
            db.add(TestAccessModelBase(id="7", lpr_id="WARIV01", lpr_country="GR", matching_version=0,
                                       access_infos={}))
            db.add(TestAccessModelBase(id="8", qr_id="QR1", access_infos={"medium_display_name": "qr"}))

        accesses = self.access_service.find_lpr_accesses(LPRMedium(id="G ARIVO 1", country=LPRCountry(code="A")))
        self.assertEqual(5, len(accesses))
        self.assertEqual({"1", "2", "3", "5", "6"}, set([a.id for a in accesses]))

        accesses = self.access_service.find_lpr_accesses(LPRMedium(id="GARIVO1"))
        self.assertEqual(3, len(accesses))
        self.assertEqual({"4", "5", "6"}, set([a.id for a in accesses]))

        accesses = self.access_service.find_lpr_accesses(LPRMedium(id="GARIV Q 1"))
        self.assertEqual(1, len(accesses))
        self.assertEqual({"6"}, set([a.id for a in accesses]))

        # we do not support edit distance in the access util function
        with self.assertRaises(AssertionError):
            self.matching_config.edit_distance = 1
            self.access_service.find_lpr_accesses(LPRMedium(id="B ARIVQ 1"))

    def test_find_qr_accesses(self):
        with self.database as db:
            db.add(TestAccessModelBase(id="1", qr_id="QR1", access_infos={"medium_display_name": "qr"}))
            db.add(TestAccessModelBase(id="2", qr_id="QR2", access_infos={"medium_display_name": "qr"}))
            db.add(TestAccessModelBase(id="3", qr_id="QR1", access_infos={"medium_display_name": "qr"}))
            db.add(TestAccessModelBase(id="4", qr_id="NFC1", access_infos={"medium_display_name": "qr"}))

        accesses = self.access_service.find_qr_accesses(QRMedium(id="QR1"))
        self.assertEqual(2, len(accesses))
        self.assertEqual("1", accesses[0].id)
        self.assertEqual("3", accesses[1].id)
        self.assertEqual({"medium_display_name": "qr"}, accesses[1].access_infos)
        accesses = self.access_service.find_qr_accesses(QRMedium(id="QR3"))
        self.assertEqual(0, len(accesses))

    def test_find_regex_accesses(self):
        with self.database as db:
            db.add(TestAccessModelBase(id="1", regex="^.+RD$", access_infos={"medium_display_name": "regex"}))
            db.add(TestAccessModelBase(id="2", regex="^BP.+$", access_infos={"medium_display_name": "regex"}))
            db.add(TestAccessModelBase(id="3", regex="^BH.+$", access_infos={"medium_display_name": "regex"}))
            db.add(TestAccessModelBase(id="4", regex="^.+RD$", access_infos={"medium_display_name": "regex"}))
            db.add(TestAccessModelBase(id="5", qr_id="QR1", access_infos={"medium_display_name": "regex"}))

        accesses = self.access_service.find_regex_accesses(LPRMedium(id="BP 123 RD"))
        self.assertEqual(3, len(accesses))
        self.assertEqual("1", accesses[0].id)
        self.assertEqual("2", accesses[1].id)
        self.assertEqual("4", accesses[2].id)
        accesses = self.access_service.find_regex_accesses(LPRMedium(id="G ARIVO 1"))
        self.assertEqual(0, len(accesses))

    def test_deduplicate(self):
        accesses = [
            AccessCheckAccess(
                id=str(i), parksettings_id="1", access_data={}, accepted=True,
                category=AccessCategory.whitelist, used_medium=QRMedium(id=""),
                access_infos={"medium_display_name": "qr"}, source="test"
            ) for i in [1, 5, 3, 4, 2, 1, 2, 3, 4, 5]
        ]
        accesses = deduplicate_accesses(accesses)
        self.assertEqual(["1", "5", "3", "4", "2"], [a.id for a in accesses])

    def test_gate_check(self):
        def create_access_dummy(id, parksettings_id, category):
            return AccessCheckAccess(
                id=id, parksettings_id=parksettings_id, access_data={}, accepted=True,
                category=category, used_medium=QRMedium(id=""),
                access_infos={"medium_display_name": "qr"}, source="test"
            )

        def create_access_dummies():
            return [create_access_dummy(id="1", parksettings_id=str(uuid.UUID(int=0)),
                                        category=AccessCategory.whitelist),
                    create_access_dummy(id="2", parksettings_id=str(uuid.UUID(int=1)),
                                        category=AccessCategory.whitelist),
                    create_access_dummy(id="6", parksettings_id=None, category=AccessCategory.whitelist),
                    create_access_dummy(id="11", parksettings_id=str(uuid.UUID(int=0)),
                                        category=AccessCategory.shortterm),
                    create_access_dummy(id="12", parksettings_id=str(uuid.UUID(int=1)),
                                        category=AccessCategory.shortterm),
                    create_access_dummy(id="16", parksettings_id=None, category=AccessCategory.shortterm)
                    ]

        self.settings.settings = {("common/gates", ""): {"gate1": Gate(gate="gate1", name="gate1", type=GateType.entry),
                                                         "gate2": Gate(gate="gate2", name="gate2", type=GateType.exit),
                                                         "gate3": Gate(gate="gate3", name="gate3", type=GateType.entry),
                                                         "door": Gate(gate="door", name="door", type=GateType.door)},
                                  ("common/parking_areas2", ""): {},
                                  ("common/parksettings2", ""): {}}

        # test door, all have access
        accesses = create_access_dummies()
        check_accesses_valid_at_gate(accesses, "door", self.settings)
        self.assertTrue(all(a.accepted for a in accesses))

        # test gate1, parksetting not found, parking_area not found
        accesses = create_access_dummies()
        check_accesses_valid_at_gate(accesses, "gate2", self.settings)
        self.assertEqual([True] * 3 + [False] * 3, [a.accepted for a in accesses])

        self.settings.settings[("common/parking_areas2", "")] = \
            {str(uuid.UUID(int=0)): ParkingArea(id=str(uuid.UUID(int=0)), name="pa0", gates=["gate1", "gate2"],
                                                shortterm_gates=["gate1"], default_cost_entries=[],
                                                shortterm_limit_type=ShorttermLimitType.no_limit, shortterm_limit=100)}

        # test gate1, parksetting not found, parking_area found and gate is shortterm gate
        accesses = create_access_dummies()
        check_accesses_valid_at_gate(accesses, "gate1", self.settings)
        self.assertTrue(all(a.accepted for a in accesses))

        # test gate2, parksetting not found, parking_area found and gate is not shortterm gate
        accesses = create_access_dummies()
        check_accesses_valid_at_gate(accesses, "gate2", self.settings)
        self.assertEqual([True] * 3 + [False] * 3, [a.accepted for a in accesses])

        self.settings.settings[("common/parksettings2", "")] = \
            {str(uuid.UUID(int=0)): Parksetting(id=str(uuid.UUID(int=0)), name="ps0", gates=["gate1"],
                                                default_cost_entries=[]),
             str(uuid.UUID(int=1)): Parksetting(id=str(uuid.UUID(int=1)), name="ps1", gates=["gate2"],
                                                default_cost_entries=[])
             }

        # test gate1, parksetting found, parking_area found and gate is shortterm gate
        # use parksetting also for shortterm if given
        accesses = create_access_dummies()
        check_accesses_valid_at_gate(accesses, "gate1", self.settings)
        self.assertEqual([True, False, True, True, False, True], [a.accepted for a in accesses])


class TestAccessCheckAccessValidators(TestCase):
    def create_access(self, category=AccessCategory.permanent, **kwargs):
        AccessCheckAccess(id="1", source="test", access_infos={}, access_data={}, accepted=True, category=category,
                          used_medium=QRMedium(id="qr"), **kwargs)

    def test_validator(self):
        with self.assertRaises(ValueError) as e:
            self.create_access(category=AccessCategory.handauf)
        self.assertIn("medium_display_name must be set if category is handauf", str(e.exception))

        with self.assertRaises(ValueError) as e:
            self.create_access(category=AccessCategory.external)
        self.assertIn("category external is not allowed for accesses", str(e.exception))

        with self.assertRaises(ValueError) as e:
            self.create_access(group_limit=1)
        self.assertIn("group_limit must not be set without group_id", str(e.exception))

        with self.assertRaises(ValueError) as e:
            self.create_access(category=AccessCategory.shortterm, group_limit=1, group_id="1")
        self.assertIn("group_limit must not be set for shortterm and unknown accesses", str(e.exception))

    def test_reject_reason_custom_validator(self):
        """This test checks if the custom validator for reject_reason works.
        If the reject_reason is set to "custom" the string field supplementary_infos must be set"""
        # correct access does not raise a validation error
        AccessCheckAccess(
            id="1", source="test", access_infos={}, access_data={}, accepted=False,
            category=AccessCategory.permanent, used_medium=QRMedium(id="qr"),
            reject_reason=AccessCheckRejectReason.custom,
            supplementary_infos="What do we say to the God of Death? Not today!"
        )
        # if supplementary_infos is null, we get a validation error
        with self.assertRaises(ValueError) as e:
            AccessCheckAccess(
                id="1", source="test", access_infos={}, access_data={}, accepted=False,
                category=AccessCategory.permanent, used_medium=QRMedium(id="qr"),
                reject_reason=AccessCheckRejectReason.custom
            )
        self.assertIn("supplementary_infos must be set if reject_reason is custom", str(e.exception))
        # an empty string also raises a validation error
        with self.assertRaises(ValueError) as e:
            AccessCheckAccess(
                id="1", source="test", access_infos={}, access_data={}, accepted=False,
                category=AccessCategory.permanent, used_medium=QRMedium(id="qr"),
                reject_reason=AccessCheckRejectReason.custom, supplementary_infos=""
            )
        self.assertIn("supplementary_infos must be set if reject_reason is custom", str(e.exception))
