import importlib
import json
import os
from collections import defaultdict
from logging import getLogger

import gspread
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone, translation
from google.oauth2.service_account import Credentials
from rest_framework.serializers import ValidationError

from .cache_models import CacheTranslation
from .enums import LanguageCodeType

logger = getLogger(__file__)


def load_callable(path: str) -> object | None:
    paths = path.split(".")
    modules = importlib.import_module(".".join(paths[:-1]))
    result = getattr(modules, paths[-1], None)
    if not result:
        logger.warning("Module does no exists. path: %s", path)
    return result


"""
from iam_service.learngual.translator import Translator
t = self = Translator(target_language="KO")
t.log_queue
"""


class Translator:
    key = "Translator-datav2"
    queue_key = "Translator-queue"

    refresh_duration = timezone.timedelta(minutes=1).total_seconds()

    def __init__(
        self,
        sheet_id=None,
        sheet_name=None,
        celery_app_path: str | None = None,
        target_language: str = None,
    ):
        if not target_language:
            target_language = translation.get_language() or "EN"
        target_language = target_language.upper()
        cache.delete_many(["Translator-data", "Translator-datav2", "Translator-queue"])
        self.sheet_id = (
            sheet_id
            or getattr(settings, "LEARNGUAL_TRANSLATE_SHEET_ID", None)
            or os.getenv("LEARNGUAL_TRANSLATE_SHEET_ID")
        )
        self.sheet_name = (
            sheet_name
            or getattr(settings, "LEARNGUAL_TRANSLATE_SHEET_NAME", None)
            or os.getenv("LEARNGUAL_TRANSLATE_SHEET_NAME")
        )

        self.celery_app_path = (
            celery_app_path
            or getattr(settings, "LEARNGUAL_CELERY_APP_PATH", None)
            or os.getenv("LEARNGUAL_CELERY_APP_PATH")
        )

        assert (
            self.sheet_id
        ), "`LEARNGUAL_TRANSLATE_SHEET_ID` must be set in enviroment variable or Django setting"
        assert (
            self.sheet_name
        ), "`LEARNGUAL_TRANSLATE_SHEET_NAME` must be set in enviroment variable or Django setting"

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = json.loads(
            getattr(settings, "LEARNGUAL_GOOGLE_BOT_GRED", None)
            or os.getenv("LEARNGUAL_GOOGLE_BOT_GRED")
            or "{}"
        )
        credentials = Credentials.from_service_account_info(creds, scopes=scopes)
        self.gc = gspread.authorize(credentials)

        self.target_language = target_language

    @property
    def translations(self):
        return self.get_cache_model().get_default_cache_model().translation

    @property
    def headers(self):
        return self.get_cache_model().get_default_cache_model().headers

    @property
    def celery_app(self):
        return load_callable(self.celery_app_path)

    def remove_duplicate_rows(self, column_name="en"):
        # Authenticate and open the Google Sheet

        sheet = self.gc.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet(self.sheet_name)

        # Get all data from the sheet
        data = worksheet.get_all_values()

        # Extract header and data rows
        header = data[0]
        rows = data[1:]

        # Find the index of the target column
        try:
            if column_name.lower() in header:
                column_index = header.index(column_name.lower())
            elif column_name.upper() in header:
                column_index = header.index(column_name.upper())
            else:
                column_index = header.index(column_name)
        except ValueError:
            raise ValueError(f"Column '{column_name}' not found in the sheet.")

        # Use a dictionary to track the last occurrence of each value in the target column
        last_occurrence = defaultdict(int)

        # Iterate through the rows to find the last occurrence of each value
        for i, row in enumerate(rows):
            value = row[column_index]
            last_occurrence[value] = i + 1  # +1 because of header

        # Build a list of row indices to keep
        rows_to_keep = set(last_occurrence.values())

        # Delete rows that are not in the rows_to_keep set
        rows_to_delete = [
            i + 2 for i in range(len(rows)) if (i + 1) not in rows_to_keep
        ]
        rows_to_delete.reverse()  # Delete from bottom to top to avoid shifting issues

        for row_index in rows_to_delete:
            worksheet.delete_rows(row_index)

        logger.info(
            f"Removed {len(rows_to_delete)} duplicate rows from column '{column_name}'."
        )

    def get_cache_model(self) -> CacheTranslation:
        return CacheTranslation

    def update_translation(self, headers, translations):

        self.get_cache_model().get_default_cache_model().update_translations(
            translations=translations, headers=headers
        )

    def update_queue(self, *texts: str):
        return self.get_cache_model().get_default_cache_model().add_to_queue(*texts)

    def overwrite_queue(self, texts: list):
        model = self.get_cache_model().get_default_cache_model()
        model.queue = texts

    def force_load_translations(self):
        logger.info("Initiate refresh tranlsations")
        try:
            self.remove_duplicate_rows()
        except Exception:
            ...
        sheet = self.gc.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet(self.sheet_name)
        data = worksheet.get_all_values()

        headers = [x.upper() for x in data[0]]
        translations = {}

        if not all([x in headers for x in ["EN", "KO"]]):
            raise ValidationError("No translation for EN or KO.")

        for row in data[1:]:
            en_value = row[0].strip()
            translations[en_value] = {
                headers[i]: row[i] for i in range(1, len(headers))
            }
        logger.info(f"Update Cache {len(translations.keys())}")
        self.update_translation(headers=headers, translations=translations)

        return translations

    def get_language_code(self, language: str) -> str:
        languages = {
            key.strip().upper(): value.strip().upper()
            for key, value in LanguageCodeType.dict_name_key().items()
        }
        if not language:
            language = "EN"
        language = language.strip().upper()
        return languages.get(language, language)

    @property
    def log_queue(self):
        return self.get_cache_model().get_default_cache_model().queue

    def get_language_list(self):
        """{
            "EN":[],
            "KO":[],
        }

        Returns:
            _type_: _description_
        """
        data = {key.upper(): [] for key in self.headers}
        data["EN"] = []
        for en_value, value in self.translations.items():
            data["EN"].append(en_value)
            for key, micro in value.items():
                if micro and key in data:
                    data[key].append(micro)

        return data

    def log_microcopy(self, text: str):
        logger.info(f"Log microcopy: {text}")
        if text not in self.translations and text:
            translations = self.translations
            headers = self.headers
            translations[text] = {headers[i]: "" for i in range(1, len(headers))}
            self.update_translation(
                **{"headers": headers, "translations": translations}
            )

            if text not in self.log_queue:
                self.update_queue(text)
                logger.info(f"Add microcopy '{text}' to log queue.")

    def log_microcopy_job(self):
        queue_list = self.log_queue

        sheet = self.gc.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet(self.sheet_name)
        data = worksheet.get_all_values()

        translations = {}
        headers = [x.upper() for x in data[0]]

        if not all([x in headers for x in ["EN", "KO"]]):
            logger.info("EN and KO column not found")
            raise ValidationError("No translation for EN and KO")

        for row in data[1:]:
            en_value = row[0].strip()
            translations[en_value] = {
                headers[i]: row[i] for i in range(1, len(headers))
            }

        queue_list = [x for x in self.log_queue if x not in translations]
        batch_to_update = queue_list[:60]
        batch_to_keep = queue_list[61:]
        if self.log_queue:
            self.overwrite_queue(batch_to_keep)
        if batch_to_update:
            logger.info(f"Added {len(batch_to_update)} microcopies to queue to sheet")
            start_index = 2
            worksheet.insert_rows([[x] for x in batch_to_update], row=start_index)

        self.force_load_translations()

    def force_add_language_column(self, language: str):
        if self.headers and language not in self.headers:
            sheet = self.gc.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet(self.sheet_name)
            # Add new column with target language header
            col_count = len(worksheet.row_values(1))
            worksheet.update_cell(1, col_count + 1, language.upper())
            logger.info(f"Added new language column: {language}")

    def add_language_column(self, language: str):
        if self.headers and language not in self.headers:
            headers: list = self.headers
            headers.append(language.upper())
            self.update_translation(
                **{"headers": headers, "translations": self.translations}
            )

            self.force_add_language_column(language=language)

    def translate(self, text: str, target_language: str):
        target_language = self.get_language_code(target_language)
        if target_language.upper() not in self.headers:
            if not self.headers:
                self.celery_app.send_task(
                    "iam.accounts.translate_load_translations",
                    routing_key="iam.accounts.translate_load_translations",
                )
            # else:
            #     self.add_language_column(target_language.upper())
            logger.debug(f"Language: {target_language} does not exists in sheet")
            return text
        stripped_text = text.strip()
        translated_dict = self.translations.get(stripped_text)
        if not translated_dict:
            if translated_dict is None:
                if text not in (
                    self.get_language_list()[self.get_language_code(target_language)]
                    or []
                ):
                    self.log_microcopy(stripped_text)
            return stripped_text

        translated_text = translated_dict.get(target_language, text)
        if not translated_text:
            return stripped_text

        return translated_text

    def get_translation(
        self, text, target_language: str | None = None, **kwargs
    ) -> str:
        target_language = target_language or self.target_language
        assert target_language, "target_language is required."
        result = self.translate(text, target_language)
        if kwargs:
            result = self.render(result, **kwargs)

        return result

    def render(self, text: str, **kwargs):
        if not text:
            return text
        try:
            return text.format(**kwargs)
        except KeyError as e:
            raise ValidationError(
                {"detail": f"Imcomplete kwargs for {kwargs} for text {text}"}
            ) from e


def translate(text, target_language: str | None = None, **kwargs) -> str:
    """Function to translate text
    use _(text)

    Args:
        text (_type_): _description_
        target_language (str | None, optional): _description_. Defaults to None.

    Returns:
        str: _description_
    """
    return Translator().get_translation(text, target_language=target_language, **kwargs)
