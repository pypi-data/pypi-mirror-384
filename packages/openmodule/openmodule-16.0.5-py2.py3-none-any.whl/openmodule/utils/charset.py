from pydantic import field_validator, Field
from pydantic import TypeAdapter

from openmodule.models.base import OpenModuleModel


class Replacement(OpenModuleModel):
    c_from: str = Field(
        validation_alias="from",
        serialization_alias="from",
    )
    c_to: str = Field(
        validation_alias="to",
        serialization_alias="to",
    )

    @field_validator("c_from")
    @classmethod
    def c_from_is_uppercase(cls, v):
        return v.upper()

    @field_validator("c_to")
    @classmethod
    def c_to_is_uppercase(cls, v):
        return v.upper()


class Charset(OpenModuleModel):
    replacements: list[Replacement] = []
    allowed: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZÄÜÖ_"

    @field_validator("allowed")
    @classmethod
    def allowed_is_uppercase(cls, v):
        return v.upper()


class CharsetConverter:
    def __init__(self, charset: Charset):
        self.replacements = charset.replacements
        self.allowed_chars = charset.allowed

    def _replace(self, text):
        for replacement in self.replacements:
            text = text.replace(replacement.c_from, replacement.c_to)
        return text

    def _remove_unknown(self, text):
        return "".join(x for x in text if x in self.allowed_chars)

    def clean(self, text):
        return self._remove_unknown(self._replace(text.upper()))


def _build_charset(allowed: str, replacements: list | tuple) -> Charset:
    return Charset(
        allowed=allowed,
        replacements=TypeAdapter(list[Replacement]).validate_python(
            {"from": f, "to": t} for f, t in replacements
        )
    )


legacy_lpr_charset = _build_charset(
    allowed="0123456789abcdefghijklmnprstuvwxyz",
    replacements=(("Ä", "A"), ("Ü", "U"), ("Ö", "O"), ("O", "0"), ("Q", "0"))
)

full_lpr_charset = _build_charset(
    allowed="0123456789ABCDEFGHIJKLMNOQPRSTUVWXYZÄÜÖ",
    replacements=((" ", ""), ("-", ""), (".", ""))
)
