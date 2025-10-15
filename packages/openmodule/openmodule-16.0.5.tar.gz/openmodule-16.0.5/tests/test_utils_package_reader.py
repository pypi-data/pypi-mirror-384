from unittest import TestCase

from openmodule.utils.package_reader import PackageReader, ConfigGetServiceByNameRequest, \
    ConfigGetInstalledServicesRequest, ConfigGetServicesByHardwareTypeRequest, ConfigGetServicesByParentTypeRequest, \
    ConfigGetServicesBySoftwareTypeRequest, ConfigGetServiceResponse, ConfigGetServicesResponse
from openmodule_test.package_reader import MockPackageReader
from openmodule_test.rpc import MockRPCClient


class MockPackageReaderTest(TestCase):
    """
    This tests the mock package reader. It is not a test for the package reader itself.
    """

    def setUp(self) -> None:
        self.reader = MockPackageReader()
        self.services = self.reader.services

    def test_parent_is_set_correctly(self):
        self.services.add_hardware_package("hw_compute_nuc_1", hardware_type=["compute"], ip="10.15.0.200")
        self.services.add_software_package("om_fancy_assistant_1", parent="hw_compute_nuc_1",
                                           env={"LOG_LEVEL": " DEBUG"})

        self.assertIsNotNone(self.reader.get_service_by_name("hw_compute_nuc_1"))
        self.assertIsNotNone(self.reader.get_service_by_name("om_fancy_assistant_1"))
        self.assertIsNotNone(self.reader.get_service_by_name("om_fancy_assistant_1").parent)
        self.assertEqual("hw_compute_nuc_1", self.reader.get_service_by_name("om_fancy_assistant_1").parent.name)

        # fake-uninstall the service, the parent must be gone
        self.services.remove("hw_compute_nuc_1")
        self.assertIsNone(self.reader.get_service_by_name("om_fancy_assistant_1").parent)

    def test_compute_id_filter(self):
        self.services.add_software_package("om_fancy_assistant_1", parent="hw_compute_nuc_1",
                                           env={"LOG_LEVEL": " DEBUG", "COMPUTE_ID": "1"})

        self.assertEqual(1, len(self.reader.list_all_services()))
        self.assertEqual(1, len(self.reader.list_all_services(compute_id=1)))
        self.assertEqual(0, len(self.reader.list_all_services(compute_id=2)))


class PackageReaderTest(TestCase):
    """
    This tests the package reader by providing a mock rpc client. The mocked responses are generated
    using the mock package reader. So
    PackageReader -> Sends RPC via MockRPCClient -> MockPackageReader -> Returns response data
    """

    def setUp(self) -> None:
        self.mock_package_reader = MockPackageReader()
        self.rpc_client = MockRPCClient(callbacks={("config", "get_service_by_name"): self.get_service_by_name,
                                                   ("config", "get_services"): self.get_services,
                                                   ("config", "get_services_by_hardware_type"):
                                                       self.get_services_by_hardware_type,
                                                   ("config", "get_services_by_parent_type"):
                                                       self.get_services_by_parent_type,
                                                   ("config", "get_services_by_software_type"):
                                                       self.get_services_by_software_type})
        self.reader = PackageReader(self.rpc_client)
        self.services = self.mock_package_reader.services

    def get_service_by_name(self, req: ConfigGetServiceByNameRequest, _):
        """
        return packages from mock_package_reader
        """
        return ConfigGetServiceResponse(service=self.mock_package_reader.get_service_by_name(req.name))

    def get_services(self, req: ConfigGetInstalledServicesRequest, _):
        """
        return packages from mock_package_reader
        """
        return ConfigGetServicesResponse(services=self.mock_package_reader.list_all_services(req.prefix))

    def get_services_by_hardware_type(self, req: ConfigGetServicesByHardwareTypeRequest, _):
        """
        return packages from mock_package_reader
        """
        return ConfigGetServicesResponse(
            services=self.mock_package_reader.list_by_hardware_type(req.hardware_type_prefix))

    def get_services_by_parent_type(self, req: ConfigGetServicesByParentTypeRequest, _):
        """
        return packages from mock_package_reader
        """
        return ConfigGetServicesResponse(services=self.mock_package_reader.list_by_parent_type(req.parent_type_prefix))

    def get_services_by_software_type(self, req: ConfigGetServicesBySoftwareTypeRequest, _):
        """
        return packages from mock_package_reader
        """
        return ConfigGetServicesResponse(
            services=self.mock_package_reader.list_by_software_type(req.software_type_prefix))

    def test_parent_is_set_correctly(self):
        self.services.add_hardware_package("hw_compute_nuc_1", hardware_type=["compute"], ip="10.15.0.200")
        self.services.add_software_package("om_fancy_assistant_1", parent="hw_compute_nuc_1", software_type=["ass"],
                                           env={"LOG_LEVEL": " DEBUG"}, parent_type=["compute"])

        self.assertIsNotNone(self.reader.get_service_by_name("hw_compute_nuc_1"))
        self.assertIsNotNone(self.reader.get_service_by_name("om_fancy_assistant_1"))
        self.assertIsNotNone(self.reader.get_service_by_name("om_fancy_assistant_1").parent)
        self.assertEqual("hw_compute_nuc_1", self.reader.get_service_by_name("om_fancy_assistant_1").parent.name)

        self.assertEqual(len(self.reader.list_all_services("om")), 1)
        self.assertEqual(len(self.reader.list_by_software_type("ass")), 1)
        self.assertEqual(len(self.reader.list_by_hardware_type("compute")), 1)
        self.assertEqual(len(self.reader.list_by_parent_type("compute")), 1)

        # fake-uninstall the service, the parent must be gone
        self.services.remove("hw_compute_nuc_1")
        self.assertIsNone(self.reader.get_service_by_name("om_fancy_assistant_1").parent)
