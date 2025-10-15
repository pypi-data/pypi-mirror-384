from unittest import TestCase

from openmodule.models.base import OpenModuleModel, Base64Payload


class Base64TestModel(OpenModuleModel):
    __test__ = False
    some_field: Base64Payload


class Base64ValidatorTest(TestCase):
    def test_correct_payload_bytes(self):
        model = Base64TestModel(some_field=b"AAAA")
        self.assertEqual(model.some_field, b"AAAA")

    def test_correct_payload_string(self):
        model = Base64TestModel(some_field="AAAA")
        self.assertEqual(model.some_field, "AAAA")

    def test_wrong_padding(self):
        with self.assertRaises(ValueError):
            Base64TestModel(some_field="AAAAA")
