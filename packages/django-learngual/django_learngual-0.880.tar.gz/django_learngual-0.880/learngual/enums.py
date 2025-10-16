import urllib.parse
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _


class ToDictChoiceHelper:
    @classmethod
    def dict(cls: type["models.TextChoices"]):
        return [
            {
                "id": uuid4().hex,
                "name": x[1],
                "value": x[0],
            }
            for x in cls.choices
        ]

    @classmethod
    def dict_name_key(cls: type["models.TextChoices"]):
        return {x[1]: x[0] for x in cls.choices}

    @classmethod
    def get_display_name(
        cls: type["models.TextChoices"], data: "LanguageCodeType"
    ) -> str:
        """Retrieve display name

        Args:
            data (LanguageCodeType): _description_

        Returns:
            str: _description_
        """
        choices = dict(cls.choices)
        return choices.get(data.value)


class LanguageCodeType(ToDictChoiceHelper, models.TextChoices):
    Azerbaijani = "az", _("Azerbaijani")
    Arabic = "ar", _("Arabic")
    Catalan = "ca", _("Catalan")
    Chinese_mandarin = "zh", _("Chinese (mandarin)")
    Czech = "cs", _("Czech")
    Danish = "da", _("Danish")
    Dutch = "nl", _("Dutch")
    English = "en", _("English")
    Esperanto = "eo", _("Esperanto")
    Finnish = "fi", _("Finnish")
    French = "fr", _("French")
    German = "de", _("German")
    Greek = "el", _("Greek")
    Hebrew = "he", _("Hebrew")
    Hindi = "hi", _("Hindi")
    Hungarian = "hu", _("Hungarian")
    Indonesian = "id", _("Indonesian")
    Irish = "ga", _("Irish")
    Italian = "it", _("Italian")
    Japanese = "ja", _("Japanese")
    Korean = "ko", _("Korean")
    Persian = "fa", _("Persian")
    Polish = "pl", _("Polish")
    Portuguese = "pt", _("Portuguese")
    Russian = "ru", _("Russian")
    Slovak = "sk", _("Slovak")
    Spanish = "es", _("Spanish")
    Swedish = "sv", _("Swedish")
    Turkish = "tr", _("Turkish")
    Ukrainian = "uk", _("Ukrainian")

    @classmethod
    def get_url(cls: type["LanguageCodeType"], data: "LanguageCodeType") -> str:
        """generate flag url

        Args:
            data (LanguageCodeType): _description_

        Returns:
            str: _description_
        """
        base_url = "https://learngual-bucket.sfo3.digitaloceanspaces.com/flags/%s.png"

        return base_url % urllib.parse.quote(
            cls.get_display_name(data) + "_" + data.value
        )
