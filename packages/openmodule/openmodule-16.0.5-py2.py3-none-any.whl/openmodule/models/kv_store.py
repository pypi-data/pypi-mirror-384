from openmodule.models.base import OpenModuleModel


class KVSetRequestKV(OpenModuleModel):
    key: str
    value: str = "null"
    e_tag: int | None = None
    previous_e_tag: int | None = None


class KVSetRequest(OpenModuleModel):
    service: str
    kvs: list[KVSetRequestKV]


class KVSetResponseKV(OpenModuleModel):
    key: str
    status: str = "error"
    error: str | None = None


class KVSetResponse(OpenModuleModel):
    pass


class KVSyncRequest(OpenModuleModel):
    service: str
    kvs: dict[str, int | None]


class KVSyncResponse(OpenModuleModel):
    additions: dict[str, int | None]
    changes: dict[str, int | None]
    missing: dict[str, int | None]


class ServerSyncResponse(OpenModuleModel):
    pass
