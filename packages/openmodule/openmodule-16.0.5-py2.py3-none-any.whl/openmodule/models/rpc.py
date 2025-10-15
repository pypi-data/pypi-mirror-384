from enum import StrEnum
from typing import Any
from uuid import UUID

from openmodule.models.base import ZMQMessage, OpenModuleModel


class RPCRequest(ZMQMessage):
    rpc_id: UUID
    resource: str | None = None
    request: dict | None = None


class RPCResponse(ZMQMessage):
    rpc_id: UUID | None = None
    response: Any = None


class RPCServerError(StrEnum):
    handler_error = "handler_error"
    validation_error = "validation_error"
    filter_error = "filter_error"
    error = "error"  # this is from RPCServer (the WebServer, not an RPCServer on the device)


class RPCErrorResult(OpenModuleModel):
    status: RPCServerError
    error: str | None = None
    exception: Any = None


class ServerRPCRequest(OpenModuleModel):
    rpc: str
    data: Any = None
