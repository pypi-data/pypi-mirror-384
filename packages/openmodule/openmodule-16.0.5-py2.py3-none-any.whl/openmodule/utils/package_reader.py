from openmodule import sentry
from openmodule.core import core
from openmodule.models.base import OpenModuleModel
from openmodule.rpc import RPCClient


class PackageData(OpenModuleModel):
    readable_name: str
    description: str
    model: str | None = None


class BaseSetting(OpenModuleModel):
    hardware_type: list[str] | None = None
    parent_type: list[str] | None = None
    software_type: list[str] | None = None
    name: str
    revision: int
    env: dict
    yml: dict
    package_data: PackageData | None = None


class ServiceSetting(BaseSetting):
    parent: BaseSetting | None = None


class ConfigGetInstalledServicesRequest(OpenModuleModel):
    """
    Request to get all installed services which start with a given predix.
    """
    compute_id: int | None = None
    prefix: str | None = ""


class ConfigGetServiceByNameRequest(OpenModuleModel):
    """
    Request a service by its name
    """
    name: str


class ConfigGetServiceResponse(OpenModuleModel):
    service: ServiceSetting | None = None


class ConfigGetServicesResponse(OpenModuleModel):
    services: list[ServiceSetting]


class ConfigGetServicesByHardwareTypeRequest(OpenModuleModel):
    """
    Request to get all services with a hardware type starting with the given prefix.
    This request always returns the configurations of the services.
    """
    compute_id: int | None = None
    hardware_type_prefix: str | None = ""


class ConfigGetServicesByParentTypeRequest(OpenModuleModel):
    """
    Returns the configs of all services for which a parent type starts with the given prefix
    Optionally you can include the parent configs in the response.
    This request always returns the configurations of the services.
    """
    compute_id: int | None = None
    parent_type_prefix: str | None = ""


class ConfigGetServicesBySoftwareTypeRequest(OpenModuleModel):
    """
    Request to get all services with a software type starting with the given prefix.
    This request always returns the configurations of the services.
    """
    compute_id: int | None = None
    software_type_prefix: str | None = ""


class PackageReader:
    def __init__(self, rpc_client: RPCClient | None = None):
        self.rpc_client = rpc_client or core().rpc_client

    @sentry.trace
    def get_service_by_name(self, service: str) -> ServiceSetting | None:
        """
        returns a service by its name
        """
        response: ConfigGetServiceResponse = self.rpc_client.rpc(
            "config", "get_service_by_name",
            ConfigGetServiceByNameRequest(name=service),
            ConfigGetServiceResponse
        )
        return response.service

    @sentry.trace
    def list_all_services(self, prefix: str | None = None, compute_id: int | None = None) -> list[ServiceSetting]:
        """
        :param prefix: prefix of the package id, if none is passed all are returned
        :param compute_id: id of the target compute unit
        """
        response: ConfigGetServicesResponse = self.rpc_client.rpc(
            "config", "get_services",
            ConfigGetInstalledServicesRequest(prefix=prefix, compute_id=compute_id),
            ConfigGetServicesResponse
        )
        return response.services

    @sentry.trace
    def list_by_hardware_type(self, prefix: str, compute_id: int | None = None) -> list[ServiceSetting]:
        """
        lists all packages with a certain hardware type (prefix). Note that these can only be hardware packages
        i.e. their name starts with "hw_"

        :param prefix: prefix of the hardware type
        :param compute_id: id of the target compute unit
        """
        response: ConfigGetServicesResponse = self.rpc_client.rpc(
            "config", "get_services_by_hardware_type",
            ConfigGetServicesByHardwareTypeRequest(hardware_type_prefix=prefix, compute_id=compute_id),
            ConfigGetServicesResponse
        )
        return response.services

    @sentry.trace
    def list_by_parent_type(self, prefix: str, compute_id: int | None = None) -> list[ServiceSetting]:
        """
        lists all packages with a certain parent type (prefix). Note that these can only be software packages
        i.e. their name starts with "om_"

        :param prefix: prefix of the parent type
        :param compute_id: id of the target compute unit
        """
        response: ConfigGetServicesResponse = self.rpc_client.rpc(
            "config", "get_services_by_parent_type",
            ConfigGetServicesByParentTypeRequest(parent_type_prefix=prefix, compute_id=compute_id),
            ConfigGetServicesResponse
        )
        return response.services

    @sentry.trace
    def list_by_software_type(self, prefix: str, compute_id: int | None = None) -> list[ServiceSetting]:
        """
        lists all packages with a certain software type (prefix). Note that these can only be software packages
        i.e. their name starts with "om_"

        :param prefix: prefix of the software type
        :param compute_id: id of the target compute unit
        """
        response: ConfigGetServicesResponse = self.rpc_client.rpc(
            "config", "get_services_by_software_type",
            ConfigGetServicesBySoftwareTypeRequest(software_type_prefix=prefix, compute_id=compute_id),
            ConfigGetServicesResponse
        )
        return response.services
