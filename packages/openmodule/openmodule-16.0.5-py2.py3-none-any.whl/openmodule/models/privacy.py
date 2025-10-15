from datetime import datetime, timedelta

from openmodule.models.base import OpenModuleModel
from openmodule.models.base import ZMQMessage
from openmodule.utils.misc_functions import utcnow


class AnonymizeMessage(ZMQMessage):
    type: str = "anonymize"
    session_id: str | None = None
    vehicle_ids: list[str] | None = []


class AnonymizeRequest(OpenModuleModel):
    session_ids: list[str]


class AnonymizeResponse(OpenModuleModel):
    pass


class PrivacyTime(OpenModuleModel):
    minutes: int | None = None
    hours: int | None = None
    days: int | None = None

    def time(self) -> datetime | None:
        kwargs = {k: v for k, v in self.model_dump().items() if v}
        return (utcnow() - timedelta(**kwargs)) if kwargs else None

    def timedelta(self) -> timedelta | None:
        kwargs = {k: v for k, v in self.model_dump().items() if v}
        return timedelta(**kwargs) if kwargs else None


class PrivacySettings(OpenModuleModel):
    paid: PrivacyTime = PrivacyTime(days=1)
    unpaid: PrivacyTime = PrivacyTime(days=90)
    registered_free: PrivacyTime = PrivacyTime(days=30)
    pay_via_invoice: PrivacyTime = PrivacyTime(days=30)
    open: PrivacyTime = PrivacyTime(days=90)
    free: PrivacyTime = PrivacyTime(minutes=5)
    honest_payment: PrivacyTime = PrivacyTime(days=90)
    erroneous: PrivacyTime = PrivacyTime(days=30)
    rejected: PrivacyTime = PrivacyTime(days=7)

    def max_timedelta(self):
        return max([x.timedelta() for x in self.__dict__.values() if isinstance(x, PrivacyTime)])
