import gettext
# create translations for these languages, first language is default
import os

from openmodule.config import settings

all_languages = ["en", "de"]

_languages = {x: gettext.translation("translation", localedir=settings.LOCALE_DIR, languages=[x])
              for x in all_languages if os.path.exists(os.path.join(settings.LOCALE_DIR, x))}

assert "en" in _languages, (
    "English language is missing, please add it to the locale directory!\n"
    "You can use the following command to create the template:\n"
    "$ openmodule_makemessages\n"
    "also ensure that the translations folder is mounted in your docker-compose.yml"
)
current_language = _languages["en"]


def _(string):
    language = _languages.get(settings.LANGUAGE)
    if language and string:
        return language.gettext(string)
    return string


def __(string_singular, string_plural, num):
    language = _languages.get(settings.LANGUAGE)
    if language:
        return language.ngettext(string_singular, string_plural, num)
    if num == 1:
        return string_singular
    else:
        return string_plural


def ___(string):
    return string


def translate(text, language_code):
    language = _languages.get(language_code)
    if language and text:
        return str(language.gettext(text))
    return text
