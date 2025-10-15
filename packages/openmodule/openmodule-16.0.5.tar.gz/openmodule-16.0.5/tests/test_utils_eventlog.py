from datetime import datetime

from openmodule.models.base import ZMQMessage
from openmodule.utils.eventlog import send_event, EventInfo, MessageKwarg, EventlogMessage, AnonymizationType, \
    PlateFormatData
from openmodule_test.core import OpenModuleCoreTestMixin


class TestEvents(OpenModuleCoreTestMixin):
    topics = ["eventlog"]

    def test_event_generation(self):
        with self.assertLogs("Eventlog") as cm:
            send_event(
                EventInfo.create("test_1", datetime.min, "gate1", "G ARIVO 1", "CH", "s1", "s2", "v1", 150),
                "LPR {lpr}: customer {name}, medium {med}, price {price}",
                lpr=MessageKwarg.lpr("G ARIVO 1", "A"), name=MessageKwarg.string("Test User"),
                med=MessageKwarg.medium("QR1"), price=MessageKwarg.price(1)
            )
        self.assertIn("INFO:Eventlog:Sending event at gate1: LPR plate='G ARIVO 1' country='A': "
                      "customer Test User, medium QR1, price 1", cm.output)

        msg = EventlogMessage.model_validate(self.zmq_client.wait_for_message_on_topic("eventlog"))
        self.assertEqual(msg.event.infos.type, "test_1")
        self.assertEqual(msg.event.infos.timestamp, datetime.min)
        self.assertEqual(msg.event.infos.gate, "gate1")
        self.assertEqual(msg.event.infos.license_plate, "G ARIVO 1")
        self.assertEqual(msg.event.infos.license_plate_country, "CH")
        self.assertEqual(msg.event.infos.session_id, "s1")
        self.assertEqual(msg.event.infos.related_session_id, "s2")
        self.assertEqual(msg.event.infos.vehicle_id, "v1")
        self.assertEqual(msg.event.infos.price, 150)
        self.assertEqual(msg.event.message, "LPR {lpr}: customer {name}, medium {med}, price {price}")
        self.assertEqual(msg.event.message_kwargs["lpr"], MessageKwarg(value=PlateFormatData(plate="G ARIVO 1",
                                                                                             country="A"),
                                                                       anonymization_type=AnonymizationType.lpr,
                                                                       format_type="lpr"))
        self.assertEqual(msg.event.message_kwargs["name"], MessageKwarg(value="Test User",
                                                                        anonymization_type=AnonymizationType.default,
                                                                        format_type="string"))
        self.assertEqual(msg.event.message_kwargs["med"], MessageKwarg(value="QR1",
                                                                       anonymization_type=AnonymizationType.medium,
                                                                       format_type="medium"))
        self.assertEqual(msg.event.message_kwargs["price"], MessageKwarg(value=1,
                                                                         anonymization_type=AnonymizationType.no,
                                                                         format_type="price"))

        with self.assertLogs("Eventlog") as cm:
            send_event(EventInfo.create("test_1"), "test")
        self.assertIn("INFO:Eventlog:Sending event: test", cm.output)
        msg = EventlogMessage.model_validate(self.zmq_client.wait_for_message_on_topic("eventlog"))
        self.assertIsNotNone(msg.event.infos.timestamp)
