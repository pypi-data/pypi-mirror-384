import datetime
import time
from textwrap import dedent
from typing import Optional
from unittest.mock import patch

import pydantic
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm import relationship

import openmodule.utils.access_service as access_utils
from openmodule.config import override_settings, override_context
from openmodule.database.custom_types import JSONEncodedDict, TZDateTime
from openmodule.models.kv_store import KVSetRequest, KVSetRequestKV, KVSyncRequest, KVSetResponse, KVSyncResponse
from openmodule.rpc import RPCServer
from openmodule.utils.kv_store import KVStore, KVEntry, KVStoreHandler
from openmodule_test.core import OpenModuleCoreTestMixin
from openmodule_test.database import SQLiteTestMixin
from openmodule_test.rpc import RPCServerTestMixin


class Base(DeclarativeBase):
    pass


class CarData(pydantic.BaseModel):
    license_plate: str
    country: str
    customer_car_id: str | None = None
    matching_scheme: str | None = None
    matching_version: int | None = None


class Contract(Base, KVEntry):
    __allow_unmapped__ = True
    __tablename__ = "contracts"

    # because the primary key of the KV entry is named 'key' we provide getter and setter for our preferred name 'id'
    @hybrid_property
    def id(self):
        return self.key

    @id.setter
    def id(self, value):
        self.key = value

    contract_id: Mapped[str]  # group id for controller
    group_limit: Mapped[Optional[int]]
    access_infos: Mapped[Optional[dict]] = mapped_column(JSONEncodedDict, nullable=True)
    barcode: Mapped[Optional[str]]  # qrcode

    # 1 to many relationship to our license plate table
    # relationship to child tables with cascade delete that deletes orphaned entries as well
    # this relationship is needed for correct deletion of the additional tables
    cars: Mapped[list["Car"]] = relationship(back_populates="contract", cascade="all, delete", passive_deletes=True)

    @classmethod
    def parse_value(cls, value: dict) -> list['Contract | Car']:
        # we validate cars json payload here with Pydantic model model_dump() function
        instances = []
        barcode = value.get("barcode")
        cars_data = value.get("cars")
        assert barcode or cars_data, "Either a barcode or cars must be present"
        contract = Contract(contract_id=value.get("contract_id"), group_limit=value.get("group_limit"),
                            access_infos=value.get("access_infos"), barcode=barcode)
        if cars_data is not None:
            # validate car json payload with Pydantic model
            cars_data = pydantic.TypeAdapter(list[CarData]).validate_python(cars_data)
            for c in cars_data:
                # you have to manually set the lpr_search_id with the clean function
                car = Car(contract=contract, lpr_id=c.license_plate,
                          lpr_search_id=access_utils.get_lpr_id_search(c.license_plate),
                          lpr_country=c.country, customer_car_id=c.customer_car_id,
                          matching_scheme=c.matching_scheme, matching_version=c.matching_version)
                instances.append(car)
        instances.append(contract)
        return instances


class Reservation(Base, KVEntry):
    __allow_unmapped__ = True
    __tablename__ = "reservations"

    # because the primary key of the KV entry is named 'key' we provide getter and setter for our preferred name 'id'
    @hybrid_property
    def id(self):
        return self.key

    @id.setter
    def id(self, value):
        self.key = value

    # a reservation has a start and an end date
    start: Mapped[datetime.datetime] = mapped_column(TZDateTime, nullable=False)
    end: Mapped[datetime.datetime] = mapped_column(TZDateTime, nullable=False)
    barcode: Mapped[str]  # qrcode

    # 1 to 1 relationship to our car table
    car: 'Car' = relationship("Car", back_populates="reservation", cascade="all, delete", passive_deletes=True,
                              uselist=False)

    @classmethod
    def parse_value(cls, value: dict) -> list['Reservation | Car']:
        # this method has to be implemented by the child class, and therefore we validate car json payload here
        # with Pydantic model model_dump() method
        instances = []
        start = datetime.datetime.fromisoformat(value["start"]) if value.get("start") else None
        end = datetime.datetime.fromisoformat(value["end"]) if value.get("end") else None
        reservation = Reservation(start=start, end=end, barcode=value.get("barcode"))
        car_data = value.pop("car", None)
        if car_data:
            car_data = CarData.model_validate(car_data)
            car = Car(reservation=reservation, lpr_id=car_data.license_plate,
                      lpr_search_id=access_utils.get_lpr_id_search(car_data.license_plate),
                      lpr_country=car_data.country, customer_car_id=car_data.customer_car_id,
                      matching_scheme=car_data.matching_scheme, matching_version=car_data.matching_version)
            instances.append(car)
        instances.append(reservation)
        return instances


class Car(Base):
    __allow_unmapped__ = True
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lpr_id: Mapped[str]
    lpr_search_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    lpr_country: Mapped[str]
    customer_car_id: Mapped[Optional[str]]
    matching_scheme: Mapped[Optional[str]]
    matching_version: Mapped[Optional[int]]

    # foreign keys to parent table - BEWARE contracts.id is just a wrapper in python!
    contract_id: Mapped[Optional[str]] = mapped_column(ForeignKey("contracts.key", ondelete="CASCADE"), nullable=True)
    contract: Mapped[Optional["Contract"]] = relationship(back_populates="cars")
    reservation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("reservations.key", ondelete="CASCADE"),
                                                          nullable=True)
    reservation: Mapped[Optional["Reservation"]] = relationship("Reservation", back_populates="car")


class KVStoreContracts(KVStore):
    database_table = Contract
    # the suffix identifies our KV store sync channel
    suffix = "contract"


class KVStoreReservations(KVStore):
    database_table = Reservation
    suffix = "reservation"


@override_settings(NAME="om_access_test_1")
class KVStoreHandlerTestCase(SQLiteTestMixin, RPCServerTestMixin, OpenModuleCoreTestMixin):
    alembic_path = "../tests/test_kv_store_multiple_database"
    database_name = "kvstore_multiple"
    rpc_channels = ["kv_sync", "rpc-websocket"]

    def setUp(self):
        super().setUp()
        self.rpc_server = RPCServer(self.zmq_context())
        self.rpc_server.run_as_thread()
        # only the kv store handler registers the RPCs
        self.kv_handler = KVStoreHandler(self.database, self.core.rpc_client, KVStoreContracts, KVStoreReservations)
        self.kv_handler.register_rpcs(self.rpc_server)
        self.wait_for_rpc_server(self.rpc_server)
        self.contract_name = "om_access_test_1_contract"
        self.reservation_name = "om_access_test_1_reservation"

    def tearDown(self):
        self.rpc_server.shutdown()
        super().tearDown()

    def test_random_offset_for_kv_stores(self):
        # we have to patch the testing() method so that the method returns something
        with patch("openmodule.utils.kv_store.testing") as mock:
            mock.return_value = False
            with override_context(NAME="Testing1"):
                offset1 = self.kv_handler._random_offset_for_sync_with_server()
            with override_context(NAME="Testing2"):
                offset2 = self.kv_handler._random_offset_for_sync_with_server()
            self.assertNotEqual(offset1, offset2)

    def test_service_name_with_suffix(self):
        self.assertEqual(self.contract_name, self.kv_handler.stores[0].service_name)
        self.assertEqual(self.reservation_name, self.kv_handler.stores[1].service_name)

    def test_kv_store_create_and_delete(self):
        set_request = KVSetRequest(service=self.contract_name, kvs=[
            KVSetRequestKV(key="test1", e_tag=1, previous_e_tag=None,
                           value=dedent("""
                           {
                            "contract_id": "0000-FEED-0000-0001",
                            "group_limit": 1,
                            "access_infos": {
                                "test": "test"
                            },
                            "cars": [
                                {
                                    "customer_car_id": "car1",
                                    "license_plate": "G:TEST1",
                                    "country": "A",
                                    "matching_scheme": "DEFAULT",
                                    "matching_version": 20
                                },
                                {
                                    "customer_car_id": "car2",
                                    "license_plate": "LÖ:TEST2",
                                    "country": "D",
                                    "matching_scheme": "DEFAULT",
                                    "matching_version": 10
                                }
                            ]
                           }
                           """)),
            KVSetRequestKV(key="test2", e_tag=2, previous_e_tag=None,
                           value=dedent("""
                           {
                            "contract_id": "Fancy Contract Id",
                            "barcode": "DEADBEEF"
                           }
                           """)),
            KVSetRequestKV(key="test3", e_tag=3, previous_e_tag=None,
                           value=dedent("""
                           {
                            "contract_id": "`o##o>",
                            "barcode": "1CE1CE1CE",
                            "cars": [
                                {
                                    "customer_car_id": "car3",
                                    "license_plate": "ASDF1",
                                    "country": "-"
                                },
                                {
                                    "customer_car_id": "car4",
                                    "license_plate": "SEMMEL1",
                                    "country": "A"
                                },
                                {
                                    "customer_car_id": "car5",
                                    "license_plate": "AMSOFA1",
                                    "country": "A"
                                }
                            ]
                           }
                           """)),
        ])
        self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
        with self.database as db:
            # check contract data
            contract = db.query(Contract).filter(Contract.id == "test1").first()
            self.assertIsNotNone(contract)
            self.assertEqual("0000-FEED-0000-0001", contract.contract_id)
            self.assertEqual(1, contract.group_limit)
            self.assertDictEqual({"test": "test"}, contract.access_infos)
            self.assertEqual(2, len(contract.cars))
            contract = db.query(Contract).filter(Contract.id == "test2").first()
            self.assertIsNotNone(contract)
            self.assertEqual("Fancy Contract Id", contract.contract_id)
            self.assertEqual("DEADBEEF", contract.barcode)
            self.assertIsNone(contract.group_limit)
            self.assertIsNone(contract.access_infos)
            self.assertEqual([], contract.cars)
            contract = db.query(Contract).filter(Contract.id == "test3").first()
            self.assertIsNotNone(contract)
            self.assertEqual("`o##o>", contract.contract_id)
            self.assertIsNone(contract.group_limit)
            self.assertIsNone(contract.access_infos)
            self.assertEqual(3, len(contract.cars))
            # check car data
            car = db.query(Car).filter(Car.lpr_search_id == "GTEST1").first()
            self.assertIsNotNone(car)
            self.assertEqual("car1", car.customer_car_id)
            self.assertEqual("G:TEST1", car.lpr_id)
            self.assertEqual("A", car.lpr_country)
            self.assertEqual("DEFAULT", car.matching_scheme)
            self.assertEqual(20, car.matching_version)
            car = db.query(Car).filter(Car.lpr_search_id == access_utils.get_lpr_id_search("LÖTEST2")).first()
            self.assertIsNotNone(car)
            self.assertEqual("car2", car.customer_car_id)
            self.assertEqual("LÖ:TEST2", car.lpr_id)
            self.assertEqual("D", car.lpr_country)
            self.assertEqual("DEFAULT", car.matching_scheme)
            self.assertEqual(10, car.matching_version)
            car = db.query(Car).filter(Car.lpr_search_id == "ASDF1").first()
            self.assertIsNotNone(car)
            self.assertEqual("car3", car.customer_car_id)
            self.assertEqual("ASDF1", car.lpr_id)
            self.assertEqual("-", car.lpr_country)
            self.assertIsNone(car.matching_scheme)
            self.assertIsNone(car.matching_version)

        # delete all entries
        set_request = KVSetRequest(service=self.contract_name, kvs=[
            KVSetRequestKV(key="test1", e_tag=None, previous_e_tag=1, value='null'),
            KVSetRequestKV(key="test2", e_tag=None, previous_e_tag=2, value='null'),
            KVSetRequestKV(key="test3", e_tag=None, previous_e_tag=3, value='null'),
        ])
        self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
        with self.database as db:
            self.assertEqual(0, db.query(Contract).count())
            self.assertEqual(0, db.query(Car).count())
            self.assertEqual(0, db.query(Reservation).count())

        # create reservation entries
        set_request = KVSetRequest(service=self.reservation_name, kvs=[
            KVSetRequestKV(key="test4", e_tag=4, previous_e_tag=None,
                           value=dedent("""
                                       {
                                        "start": "2023-09-05T17:57:12",
                                        "end": "2023-09-05T19:00:00",
                                        "barcode": "C0FFEE",
                                        "car": {
                                            "license_plate": "RESERVATION1",
                                            "country": "-"
                                        }
                                       }
                                       """)),
            KVSetRequestKV(key="test5", e_tag=5, previous_e_tag=None,
                           value=dedent("""
                                   {
                                     "start": "2000-01-01T12:12:12",
                                     "end": "2001-01-01T01:01:01",
                                     "barcode": "BARCODE",
                                     "car": {
                                          "license_plate": "RESERVATION2",
                                          "country": "-"
                                     }
                                   }
                                   """)),

        ])
        self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
        with self.database as db:
            # check reservation data
            reservation = db.query(Reservation).filter(Reservation.id == "test4").first()
            self.assertIsNotNone(reservation)
            self.assertIsNotNone(reservation.start)
            self.assertTrue(isinstance(reservation.start, datetime.datetime))
            self.assertIsNotNone(reservation.end)
            self.assertTrue(isinstance(reservation.end, datetime.datetime))
            self.assertEqual("C0FFEE", reservation.barcode)
            self.assertEqual(reservation.car.lpr_id, "RESERVATION1")
            self.assertEqual(reservation.car.lpr_search_id, access_utils.get_lpr_id_search("RESERVATION1"))
            self.assertEqual(reservation.car.lpr_country, "-")
            self.assertIsNone(reservation.car.customer_car_id)
            self.assertIsNone(reservation.car.contract)
            self.assertIsNone(reservation.car.matching_scheme)
            self.assertIsNone(reservation.car.matching_version)
            reservation = db.query(Reservation).filter(Reservation.id == "test5").first()
            self.assertIsNotNone(reservation)
            self.assertIsNotNone(reservation.start)
            self.assertTrue(isinstance(reservation.start, datetime.datetime))
            self.assertIsNotNone(reservation.end)
            self.assertTrue(isinstance(reservation.end, datetime.datetime))
            self.assertEqual("BARCODE", reservation.barcode)
            self.assertEqual(reservation.car.lpr_id, "RESERVATION2")
            self.assertEqual(reservation.car.lpr_search_id, access_utils.get_lpr_id_search("RESERVATION2"))
            self.assertEqual(reservation.car.lpr_country, "-")
            self.assertIsNone(reservation.car.customer_car_id)
            self.assertIsNone(reservation.car.contract)
            self.assertIsNone(reservation.car.matching_scheme)
            self.assertIsNone(reservation.car.matching_version)

        # delete all reservations
        set_request = KVSetRequest(service=self.reservation_name, kvs=[
            KVSetRequestKV(key="test4", e_tag=None, previous_e_tag=4, value='null'),
            KVSetRequestKV(key="test5", e_tag=None, previous_e_tag=5, value='null'),
        ])
        self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
        with self.database as db:
            self.assertEqual(0, db.query(Reservation).count())
            self.assertEqual(0, db.query(Car).count())
            self.assertEqual(0, db.query(Contract).count())

    def test_kv_store_update(self):
        # contracts
        set_request = KVSetRequest(service=self.contract_name, kvs=[
            KVSetRequestKV(key="test1", e_tag=1, previous_e_tag=None,
                           value=dedent("""
                                   {
                                    "contract_id": "0000-FEED-0000-0001",
                                    "group_limit": 1,
                                    "access_infos": {
                                        "test": "test"
                                    },
                                    "cars": [
                                        {
                                            "customer_car_id": "car1",
                                            "license_plate": "G:TEST1",
                                            "country": "A",
                                            "matching_scheme": "DEFAULT",
                                            "matching_version": 20
                                        }
                                    ]
                                   }
                                   """)),
        ])
        self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
        with self.database as db:
            self.assertEqual(1, db.query(Contract).count())
            self.assertEqual(1, db.query(Car).count())
        set_request = KVSetRequest(service=self.contract_name, kvs=[
            KVSetRequestKV(key="test1", e_tag=2, previous_e_tag=1,
                           value=dedent("""
                                           {
                                            "contract_id": "0000-FEED-0000-0002",
                                            "group_limit": 0,
                                            "access_infos": {},
                                            "cars": [
                                                {
                                                    "customer_car_id": "car2",
                                                    "license_plate": "LÖ:TEST1",
                                                    "country": "D",
                                                    "matching_scheme": "LEGACY",
                                                    "matching_version": 0
                                                }
                                            ]
                                           }
                                           """)),
        ])
        self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
        with self.database as db:
            self.assertEqual(1, db.query(Contract).count())
            self.assertEqual(1, db.query(Car).count())
            contract = db.query(Contract).filter(Contract.id == "test1").first()
            self.assertEqual("0000-FEED-0000-0002", contract.contract_id)
            self.assertEqual(0, contract.group_limit)
            self.assertDictEqual({}, contract.access_infos)
            car = db.query(Car).filter(Car.lpr_search_id == access_utils.get_lpr_id_search("LÖ TEST1")).first()
            self.assertEqual("car2", car.customer_car_id)
            self.assertEqual("LÖ:TEST1", car.lpr_id)
            self.assertEqual("D", car.lpr_country)
            self.assertEqual("LEGACY", car.matching_scheme)
            self.assertEqual(0, car.matching_version)

        # we flush our database and test update for reservation
        with self.database as db:
            db.query(Car).delete()
            db.query(Contract).delete()

        set_request = KVSetRequest(service=self.reservation_name, kvs=[
            KVSetRequestKV(key="test2", e_tag=3, previous_e_tag=None,
                           value=dedent("""
                                       {
                                        "start": "2023-09-05T17:57:12",
                                        "end": "2023-09-05T19:00:00",
                                        "barcode": "1CE1CE-BABY",
                                        "car": {
                                            "license_plate": "UNKNOWN1",
                                            "country": "-"
                                        }
                                       }
                                       """)),

        ])
        self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
        with self.database as db:
            self.assertEqual(1, db.query(Reservation).count())
            self.assertEqual(1, db.query(Car).count())

        set_request = KVSetRequest(service=self.reservation_name, kvs=[
            KVSetRequestKV(key="test2", e_tag=4, previous_e_tag=3,
                           value=dedent("""
                                       {
                                        "start": "2000-01-01T00:00:00",
                                        "end": "2023-12-31T23:59:59",
                                        "barcode": "PikaPika",
                                        "car": {
                                            "license_plate": "G:ASDF1",
                                            "country": "A"
                                        }
                                       }
                                       """)),

        ])
        self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
        with self.database as db:
            self.assertEqual(1, db.query(Reservation).count())
            self.assertEqual(1, db.query(Car).count())
            reservation = db.query(Reservation).filter(Reservation.id == "test2").first()
            self.assertEqual(datetime.datetime(2000, 1, 1, 0, 0, 0), reservation.start)
            self.assertEqual(datetime.datetime(2023, 12, 31, 23, 59, 59), reservation.end)
            self.assertEqual("PikaPika", reservation.barcode)
            car = db.query(Car).filter(Car.lpr_search_id == "GASDF1").first()
            self.assertEqual(car.lpr_id, "G:ASDF1")
            self.assertEqual(car.lpr_country, "A")

    def test_kv_store_rpc_filtering(self):
        # contracts
        with self.database as db:
            contract = Contract(contract_id="contractId", group_limit=1, access_infos={}, barcode=None, key="key1",
                                e_tag=1)
            car = Car(contract=contract, lpr_id="GTEST1", lpr_search_id="GTEST1", lpr_country="A")
            db.add(contract)
            db.add(car)
        response: KVSyncResponse = self.rpc("kv_sync", "sync",
                                            KVSyncRequest(service=self.contract_name, kvs={}),
                                            KVSyncResponse)
        self.assertEqual(1, len(response.additions.keys()))
        # reservation
        with self.database as db:
            reservation = Reservation(start=datetime.datetime.now(), end=datetime.datetime.now(), barcode="CODE",
                                      key="key2", e_tag=1)
            car = Car(reservation=reservation, lpr_id="GTEST1", lpr_search_id="GTEST1", lpr_country="A")
            db.add(reservation)
            db.add(car)
        response: KVSyncResponse = self.rpc("kv_sync", "sync",
                                            KVSyncRequest(service=self.reservation_name, kvs={}),
                                            KVSyncResponse)
        self.assertEqual(1, len(response.additions.keys()))
        # unknown suffix, therefore RPC should not be answered, and it runs into a timeout
        with self.assertRaises(TimeoutError):
            self.rpc("kv_sync", "sync", KVSyncRequest(service="unknown_suffix", kvs={}), KVSyncResponse)

    def test_kv_store_start_and_shutdown(self):
        # we run our kv store handler as thread
        self.kv_handler.run_as_thread()

        # we wait a little until all kv stores are running
        time.sleep(0.1)

        # the shutdown function should kill all running instances of the stores
        # timout has to be 3 seconds because of the default timeout of the rpc client
        # the run method uses the method ConnectionStatusListener.get_current_status() which is a blocking call
        self.kv_handler.shutdown(timeout=3)
        self.assertFalse(self.kv_handler.running)

    def test_adding_stores_with_same_suffix_raises_exception(self):
        class KVStoreTest(KVStore):
            database_table = Contract

        with self.assertRaises(AssertionError):
            kv = KVStoreHandler(self.database, self.core.rpc_client, KVStoreContracts)
            kv.add_kvstore(KVStoreReservations)
            kv.add_kvstore(KVStoreContracts)
        with self.assertRaises(AssertionError):
            kv = KVStoreHandler(self.database, self.core.rpc_client, KVStoreReservations)
            kv.add_kvstore(KVStoreContracts)
            kv.add_kvstore(KVStoreReservations)
        with self.assertRaises(AssertionError):
            KVStoreHandler(self.database, self.core.rpc_client, KVStoreTest, KVStoreTest)

    def test_adding_stores_after_run_as_thread_raises_exception(self):
        self.kv_handler.run_as_thread()

        with self.assertRaises(AssertionError):
            self.kv_handler.add_kvstore(KVStoreReservations)

        self.kv_handler.shutdown()
