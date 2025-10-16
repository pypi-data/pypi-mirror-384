import importlib
import json
import logging
import mimetypes
import os
import re
import subprocess
import tempfile
import urllib.parse
from collections import OrderedDict
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timedelta
from logging import getLogger
from pathlib import Path
from typing import Any, Literal, TypedDict
from unittest.mock import patch
from urllib.parse import urlparse

import jwt
import pytz
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.db import models
from django.db.models import Q, QuerySet
from django.http import HttpRequest, QueryDict
from django.utils import timezone, translation
from django_filters.rest_framework import DjangoFilterBackend
from faker import Faker
from requests import Session, exceptions
from requests.adapters import HTTPAdapter, Retry
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter

from .enums import LanguageCodeType
from .translator import Translator

requests = Session()
retries = Retry(total=2, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
requests.mount("http://", HTTPAdapter(max_retries=retries))


faker = Faker()

logger = getLogger(__file__)

LEARNGUAL_SERVICE_API_KEY = getattr(
    settings, "LEARNGUAL_SERVICE_API_KEY", None
) or os.getenv("LEARNGUAL_SERVICE_API_KEY", None)


LOCAL_URLS = {
    "iam": "http://django-iam:8000",
    "learn": "http://django-learn:8000",
    "payment": "http://django-pay:8000",
    "notify": "http://django-notify:8000",
    "media": "http://django-media:8000",
    "node": "http://node_service:8000",
}


def transform_local_base_url(
    base_url: str,
    service: Literal["payment", "iam", "learn", "notify", "media"] = "iam",
) -> str:
    """check if baser_url is local url return the approprate url

    Args:
        base_url (str): _description_
        service
              _description_. Defaults to "iam".

    Returns:
        str: _description_
    """
    if not base_url.startswith("https://"):
        return LOCAL_URLS.get(service, "iam")
    return base_url


def get_service_request_headers(**kwargs) -> dict:
    """function add headers needed for request made from a service

    Returns:
        dict: _description_
    """
    if LEARNGUAL_SERVICE_API_KEY:
        kwargs["service-key"] = LEARNGUAL_SERVICE_API_KEY

    return {**kwargs}


def get_service_request_params(**kwargs) -> str:
    """function return query params needed to make request as a service

    Returns:
        dict: _description_
    """

    if LEARNGUAL_SERVICE_API_KEY:
        kwargs["_service-key"] = LEARNGUAL_SERVICE_API_KEY
    if not kwargs:
        return ""
    return "?" + "&".join([f"{x}={y}" for x, y in kwargs.items()])


def get_nested_value(data: dict[str, Any], path: str):
    """
    Retrieve a nested dictionary value using a dot path, including support for accessing lists and slicing.

    Args:
        data (Dict[str, Any]): The nested dictionary to traverse.
        path (str): The dot-separated path to the desired value.

    Returns:
        The value at the specified path if found, otherwise None.

    Example:
        data = {
            'foo': {
                'bar': [
                    {'baz': 42},
                    {'qux': [1, 2, 3, 4, 5]}
                ]
            }
        }

        result = get_nested_value(data, 'foo.bar[0].baz')
        # Output: 42

        result = get_nested_value(data, 'foo.bar[1].qux[2]')
        # Output: 3

        result = get_nested_value(data, 'foo.bar[1].qux[1:4]')
        # Output: [2, 3, 4]

        result = get_nested_value(data, 'foo.bar[1].qux[:3]')
        # Output: [1, 2, 3]

        result = get_nested_value(data, 'foo.bar[1].qux[2:]')
        # Output: [3, 4, 5]

        result = get_nested_value(data, 'foo.bar[1].qux[5]')
        # Output: None (Index out of range)

        result = get_nested_value(data, 'foo.bar[1].qux[4:2]')
        # Output: None (Invalid slice range)
    """
    keys = path.split(".")
    value = data

    try:
        for key in keys:
            if key.endswith("]"):
                key, index_or_slice = key[:-1].split("[")
                if ":" in index_or_slice:
                    start, stop = map(int, index_or_slice.split(":"))
                    value = value[key][start:stop]
                else:
                    index = int(index_or_slice)
                    value = value[key][index]
            else:
                value = value[key]
    except (KeyError, TypeError, IndexError, ValueError):
        value = None
        logging.warning(f"Could not retrieve path:'{path}'.")

    return value


def update_nested_value(data: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    """
    Update a nested dictionary value using a dot path and return the modified dictionary.

    Args:
        data (Dict[str, Any]): The nested dictionary to update.
        path (str): The dot-separated path to the value to update.
        value (Any): The new value to assign.

    Returns:
        Dict[str, Any]: The modified dictionary.

    Example:
        data = {
            'foo': {
                'bar': {
                    'baz': 42
                }
            }
        }

        updated_data = update_nested_value(data, 'foo.bar.baz', 99)
        # Now, updated_data['foo']['bar']['baz'] is 99

        updated_data = update_nested_value(data, 'foo.bar.qux', [1, 2, 3])
        # Now, updated_data['foo']['bar']['qux'] is [1, 2, 3]
    """
    keys = path.split(".")
    current_dict = data

    for key in keys[:-1]:
        if key not in current_dict or not isinstance(current_dict[key], dict):
            current_dict[key] = {}
        current_dict = current_dict[key]

    current_dict[keys[-1]] = value
    return data


def extract_base_url(url):
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme + "://" + parsed_url.netloc
    return base_url


def flatten_dict(
    data: dict[str, Any], parent_key: str = "", sep: str = "."
) -> dict[str, Any]:
    """
    Flatten a nested dictionary into a new dictionary with dot path keys.

    Args:
        data (Dict[str, Any]): The nested dictionary to flatten.
        parent_key (str): The parent key to use for the current level of the dictionary (used recursively).
        sep (str): The separator to use between the parent key and the current key.

    Returns:
        Dict[str, Any]: The flattened dictionary with dot path keys.

    Example:
        data = {
            'foo': {
                'bar': {
                    'baz': 42
                },
                'qux': [1, 2, 3]
            },
            'hello': 'world'
        }

        flattened_data = flatten_dict(data)
        # flattened_data is:
        # {
        #     'foo.bar.baz': 42,
        #     'foo.qux': [1, 2, 3],
        #     'hello': 'world'
        # }
    """
    flattened = {}
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            flattened.update(flatten_dict(value, new_key, sep=sep))
        else:
            flattened[new_key] = value
    return flattened


def unflatten_dict(data: dict[str, Any], sep: str = ".") -> dict[str, Any]:
    """
    Convert a dictionary with dot path keys to a nested dictionary.

    Args:
        data (Dict[str, Any]): The dictionary with dot path keys to convert.
        sep (str): The separator used in the dot path keys.

    Returns:
        Dict[str, Any]: The nested dictionary.

    Example:
        data = {
            'foo.bar.baz': 42,
            'foo.qux': [1, 2, 3],
            'hello': 'world'
        }

        nested_data = unflatten_dict(data)
        # nested_data is:
        # {
        #     'foo': {
        #         'bar': {
        #             'baz': 42
        #         },
        #         'qux': [1, 2, 3]
        #     },
        #     'hello': 'world'
        # }
    """
    nested = {}
    for key, value in data.items():
        parts = key.split(sep)
        current_dict = nested
        for part in parts[:-1]:
            if part not in current_dict:
                current_dict[part] = {}
            current_dict = current_dict[part]
        current_dict[parts[-1]] = value
    return nested


class PermissonUtils:
    def __init__(self, permission: dict) -> None:
        """
        Example: {
            "id":1223344
            "metadata":{

            }
        }

        Args:
            permission (dict): _description_
        """
        assert type(permission) == dict, "permssion must be a dictionary"
        self.__permission = permission

    def to_dict(self) -> dict:
        """return a dictionary of modified permission

        Returns:
            dict: _description_
        """
        return self.__permission

    def to_flat_dict(
        self, parent_key: str = "", sep: str = ".", *args, **kwargs
    ) -> dict:
        """return a flat dictionary of modified permission

        Example:
        data = {
            'foo': {
                'bar': {
                    'baz': 42
                },
                'qux': [1, 2, 3]
            },
            'hello': 'world'
        }

        flattened_data = flatten_dict(data)
        # flattened_data is:
        # {
        #     'foo.bar.baz': 42,
        #     'foo.qux': [1, 2, 3],
        #     'hello': 'world'
        # }

        Returns:
            dict: _description_
        """
        return flatten_dict(
            self.to_dict(), parent_key=parent_key, sep=sep, *args, **kwargs
        )

    def bool(self, path: str):
        """retrieve a boolean value from a nested dictionary

        Args:
            path (str): Example: metadata.manage_course.value

        Returns:
            bool|None: _description_
        """
        res = get_nested_value(self.__permission, path)
        if res is not None:
            return str(res).strip().lower() in ["true", "1"] or res

    def int(self, path: str) -> int:
        """retrieve a boolean value from a nested dictionary

        Args:
            path (str): Example: metadata.request_count.value

        Returns:
            int: _description_
        """
        res = get_nested_value(self.__permission, path)
        try:
            return int(res or 0)
        except (ValueError, TypeError):
            return int()

    def float(self, path: str) -> float:
        """retrieve a boolean value from a nested dictionary

        Args:
            path (str): Example: metadata.audio_seconds.value

        Returns:
            float: _description_
        """
        res = get_nested_value(self.__permission, path)
        try:
            return float(res or 0)
        except (ValueError, TypeError):
            return float()

    def set_value(self, path: str, value: Any, force_create: bool = False) -> dict:
        """function is used to overwrite key in the permission

        Args:
            path (str): _description_
            value Any: Example: 10, -30, {"age":12}
            force_create (bool, optional): _description_. Defaults to False.

        Raises:
            KeyError: if key does not exist and force_create is equal to false

        Returns:
            dict: _description_
        """

        res = get_nested_value(self.__permission, path)

        if res is None and not force_create:
            raise KeyError(f"{path} does not exists")
        return update_nested_value(self.__permission, path, value)

    def add_number(self, path: str, number, force_create: bool = False) -> dict:  # noqa
        """function is used to increment or decrement

        Args:
            path (str): _description_
            number (float | int): Example: 10, -30
            force_create (bool, optional): _description_. Defaults to False.

        Raises:
            TypeError: if wrong type is passed as number
            KeyError: if key does not exist and force_create is equal to false

        Returns:
            dict: _description_
        """
        if type(number) == str and str(number).isdigit():
            number = float(number)

        res = get_nested_value(self.__permission, path)

        if res is None and not force_create:
            raise KeyError(f"{path} does not exists")

        if type(number) in [int, float]:
            data = (res + number) if type(res) in [int, float] else 0 + number
            return update_nested_value(self.__permission, path, data)
        else:
            raise TypeError(f"{number} must be of type int ot float")


class PermissionManager:
    def update_permission_with_event(
        self, event_name, routing_key, permission_data, permission_id
    ):
        ...

    def update_permission_with_api(
        self,
        base_url: str,
        permission_id,
        service: Literal["iam", "payment", "notify", "learn", "media"] = "iam",
        permmission_data=dict(),
        headers: dict = dict(),
        params: str = "",
    ):
        """_summary_

        Args:
            base_url (str): _description_
            permission_id (_type_): _description_
            service (Literal["iam", "payment", "notify", "learn", "media"], optional): _description_. Defaults to "iam".
            permmission_data (_type_, optional): _description_. Defaults to dict().
            headers (dict, optional): _description_. Defaults to dict().
            params (str, optional): e.g name=aka&age=201. Defaults to "".

        Raises:
            exceptions.RequestException: _description_

        Returns:
            _type_: _description_
        """
        if not str(base_url or "").startswith("https://"):
            base_url = LOCAL_URLS.get(service) or LOCAL_URLS.get("iam")

        params = params.strip("?")
        params = dict([x.split("=") for x in params.split("&")])
        headers = get_service_request_headers(**headers)

        url_path = f"/{service}/v1/permissions/{permission_id}/"
        res = requests.patch(
            base_url.rstrip("/") + url_path + get_service_request_params(**params),
            json=permmission_data,
            headers=headers,
        )
        if not res.ok:
            try:
                response_detail = res.json().get("detail")
            except exceptions.JSONDecodeError:
                response_detail = None

            if response_detail == "Invalid service key":
                logger.error(f"invalid service key, headers={headers}")
                raise exceptions.RequestException("invalid service key")
            elif response_detail == "account does not exist":
                logger.error(
                    f"Account does not exist, {response_detail =}, {service =}"
                )
                raise exceptions.RequestException(
                    f"Account does not exist in {service} service."
                )
            else:
                logger.error("permission service is down %s", res.content)
                raise exceptions.RequestException(
                    dict(error="permission service is down", response=res.content)
                )
        return res.json()

    def clear_cache(
        self,
        *,
        service: Literal["iam", "payment", "notify", "learn", "media"] = "iam",
        permission_id: str,
    ):
        """clear cache

        Args:
            permission_id (str): _description_
            service (Literal["iam", "payment", "notify", "learn", "media"], optional): _description_. Defaults to "iam".
        """
        url_path = f"/{service}/v1/service/permissions/{permission_id}/"
        cache.delete(url_path)

    def retrieve_permission(
        self,
        *,
        base_url: str,
        permission_id: str,
        service: Literal["iam", "payment", "notify", "learn", "media"] = "iam",
        dot_path: str = None,
        headers: dict = dict(),
        params: str = "",
        cache_timeout: float = timezone.timedelta(seconds=10).total_seconds(),
    ):
        """_summary_

        Args:
            permission_id (str): example: '123456', 'sdGh66gGGHgfadsty', 'product:1234567'
            service (_type_): "iam" | "pay" | "notify" | "learn" | "media"
            base_url (str):
            dot_path (str):Default:None, e.g metadata.request_count.value
            headers (dict):Default:{}
            params (str):Default:"", e.g name=ann&age=102
            cache_timeout (float):Default:timezone.timedelta(hours=1).total_seconds()
        """
        url_path = f"/{service}/v1/service/permissions/{permission_id}/"
        if not str(base_url or "").startswith("https://"):
            base_url = LOCAL_URLS.get(service) or LOCAL_URLS.get("iam")
        data = cache.get(url_path)

        params = params.strip("?")
        params = dict([x.split("=") for x in params.split("&") if x])

        if not data:
            headers = get_service_request_headers(**headers)
            res = requests.get(
                base_url.rstrip("/") + url_path + get_service_request_params(**params),
                headers=headers,
            )
            if not res.ok:
                try:
                    response_detail = res.json().get("detail")
                except exceptions.JSONDecodeError:
                    response_detail = None

                if response_detail == "Invalid service key":
                    logger.error(f"invalid service key, headers={headers}")
                    raise exceptions.RequestException("invalid service key")
                elif response_detail == "account does not exist":
                    logger.error(
                        f"Account does not exist, {response_detail =}, {service =}"
                    )
                    raise exceptions.RequestException(
                        f"Account does not exist in {service} service."
                    )
                else:
                    logger.error("permission service is down %s", res.content)
                    raise exceptions.RequestException(
                        dict(error="permission service is down", response=res.content)
                    )
            data = {}
            try:
                data = res.json()
                cache.set(url_path, data, timeout=cache_timeout)
            except exceptions.JSONDecodeError:
                logger.info(f"Permission service unavailable: {res.content}")
                raise exceptions.RequestException(
                    dict(error="permission service is down", response=res.content)
                )

        if dot_path:
            return get_nested_value(data, dot_path)
        return data


class TestHelper:
    permission_request_path = "iam_service.learngual.utils.requests.get"
    developer_permission = {
        "metadata": {
            "is_free": {"value": False},
            "subscription_expired": {"value": False, "state": "ACTIVE"},
            "subscription_expired_at": {
                "value": (timezone.now() + timezone.timedelta(days=30)).isoformat()
            },
            "request_count_request_limit_audio_seconds": {
                "price_per_api_call": 1,
                "request_limit_count": 23,
                "excess_price_per_api": 2,
                "audio_duration": 500,
            },
            "IELTS_TOEFL_standard_grading": {"value": True},
            "ai_speech_analysis": {"value": True},
            "speech_analysis": {"value": True},
            "multiple_language_translation": {"Value": "True"},
            "access_to_learngual_features": {"value": True},
            "tech_support": {"Value": "True"},
            "grace_period_ended": {"value": False},
            "grammar_character_limit": {"value": 4000},
            "relevance_character_limit": {"value": 4000},
        }
    }

    developer_permission_grace_period = {
        "metadata": {
            "is_free": {"value": False},
            "subscription_expired": {"value": True, "state": "GRACE PERIOD"},
            "subscription_expired_at": {
                "value": (timezone.now() - timezone.timedelta(days=1)).isoformat()
            },
            "request_count_request_limit_audio_seconds": {
                "price_per_api_call": 1,
                "request_limit_count": 23,
                "excess_price_per_api": 2,
            },
            "IELTS_TOEFL_standard_grading": {"value": True},
            "ai_speech_analysis": {"value": True},
            "speech_analysis": {"value": True},
            "multiple_language_translation": {"Value": "True"},
            "access_to_learngual_features": {"value": True},
            "tech_support": {"Value": "True"},
            "grace_period_ended": {"value": False},
        }
    }

    def generate_timedelta(
        self,
        when: Literal["before", "after"],
        period: Literal["weeks", "days", "minutes", "seconds"] = "days",
        value: int = 2,
    ) -> str:
        """
        Args:
            when (Literal["before", "after"]): description
            period (Literal["weeks", "days", "minutes", "seconds"]): description
            value (int): description
        """
        if when == "before":
            return (
                (timezone.now() - timezone.timedelta(**{period: value}))
                .date()
                .isoformat()
            )
        elif when == "after":
            return (
                (timezone.now() + timezone.timedelta(**{period: value}))
                .date()
                .isoformat()
            )

    def no_duplicate(
        self, data: list[str | int] | list[dict[str, Any]], id_field: str | int = "id"
    ) -> bool:
        if not data:
            return True
        if type(data[0]) in [dict, OrderedDict]:
            data = [x.get(id_field) for x in data]
        return len(data) == len(set(data))

    def has_no_duplicate_in_response_results(
        self, response, id_field: str | int = "id"
    ) -> bool:
        data: list[str | int] | list[dict[str, Any]] = response.data.get("results")
        if not data:
            return True
        if type(data[0]) in [dict, OrderedDict]:
            data = [x.get(id_field) for x in data]
        return len(data) == len(set(data))

    def has_fields(self, data: dict, fields: list[int | str]) -> bool:
        conditions = []
        for x in fields:
            exist = x in data
            conditions.append(exist)
            if not exist:
                logging.warning("field -> '%s' does not exists", x)
        return all(conditions)

    def extract_results_in_response(self, response) -> list[dict]:
        return response.data.get("results")

    def has_fields_in_response_results(self, response, fields: list[int | str]) -> bool:
        results: list[dict] = response.data.get("results")
        if not results:
            return False
        data: dict = results[0]
        conditions = []
        for x in fields:
            exist = x in data
            conditions.append(exist)
            if not exist:
                logging.warning("field -> '%s' does not exists", x)
        return all(conditions)

    def has_paginated_count(self, response, count: int) -> bool:
        return response.data.get("count") == count

    def has_response_status(self, response, status_code: int) -> bool:
        return response.status_code == status_code

    def add_query_params_to_url(self, url: str, params: dict[str, Any]) -> str:
        query_string = urllib.parse.urlencode(params)
        return f"{url}?{query_string}"

    @contextmanager
    def mock_permission_context(self, permissions=None):
        if permissions is None:
            permissions = {}
        with patch(self.permission_request_path) as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {
                **self.developer_permission,
                **permissions,
            }
            yield mock_get


def get_timezone_from_country(country_code) -> str:
    try:
        country_timezones = pytz.country_timezones.get(country_code.upper())
        if country_timezones:
            # Assuming the first timezone for simplicity
            return pytz.timezone(country_timezones[0])
        else:
            return None  # Country code not found or no timezone information available
    except KeyError:
        return None  # Invalid country code


def get_base_url(
    service: Literal["iam", "payment", "learn", "notify", "media"] = "iam"
):
    url: str = settings.LEARNGUAL_AUTH_RETRIEVE_URL
    if "learngual.com" not in url:
        url = LOCAL_URLS.get(service) or LOCAL_URLS.get("iam")

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url


def extract_jwt_payload(refresh_token, secret_key):
    """Extracts the payload from a JWT refresh token.

    Args:
        refresh_token: The JWT refresh token.
        secret_key: The secret key used to decode the token.

    Returns:
        The decoded payload as a dictionary, or None if decoding fails.
    """

    try:
        decoded_token = jwt.decode(
            refresh_token, secret_key, algorithms=["HS256"]
        )  # Replace 'HS256' with your algorithm
        return decoded_token
    except jwt.exceptions.InvalidTokenError:
        return {}


def _translate(text: str, target_language: str = "EN", **kwargs):
    """Function to help translate micro-copies

    Args:
        text (str): _description_
        target_language (str): _description_

    Returns:
        _type_: _description_
    """
    return Translator().get_translation(text, target_language, **kwargs)


def extract_language_from_context(context: dict[str, Any]) -> str:
    """Function to extract language from serializer context

    Args:
        context (dict[str,Any]): _description_

    Returns:
        str: _description_
    """
    language = "EN"
    if context:
        request = context.get("request")
        if request:

            if translation.get_language().lower() not in ["en", "en_us", "en-us"]:
                language = translation.get_language()
            elif account := (
                getattr(request, "account", None)
                or getattr(request.user, "account", None)
            ):
                language = account.language
            elif request.user.is_authenticated:
                language = request.user.language
            else:
                language = request.GET.get("_lang")
    return language


def load_callable(path: str) -> object | None:
    paths = path.split(".")
    modules = importlib.import_module(".".join(paths[:-1]))
    result = getattr(modules, paths[-1], None)
    if not result:
        logger.warning("Module does no exists. path: %s", path)
    return result


def get_language_code(language: str) -> str:
    languages = {
        key.strip().upper(): value.strip().upper()
        for key, value in LanguageCodeType.dict_name_key().items()
    }
    if not language:
        language = "EN"
    language = language.strip().upper()
    return languages.get(language, language)


@contextmanager
def with_language(lang):
    """
    A context manager that activates the provided language for the duration
    of the context block and reverts it to the previous language afterward.
    """
    # Get the current language
    current_language = translation.get_language()
    # Activate the new language
    if lang:
        translation.activate(get_language_code(lang))
    try:
        yield
    finally:
        # Revert to the previous language
        translation.activate(current_language)


class MediaFileInfo(TypedDict, total=False):
    mime_type: str | None  # MIME type (optional)
    duration: str  # Duration as a string (e.g., "00:00:00.000")
    duration_obj: timedelta  # Duration as a timedelta object
    video_codec: str | None  # Video codec (optional, only for video files)
    resolution: str | None  # Resolution (optional, only for video files)
    frame_rate: str | None  # Frame rate (optional, only for video files)
    audio_codec: str | None  # Audio codec (optional, for audio/video files)
    bitrate: str | None  # Bitrate (optional, for audio/video files)
    sample_rate: str | None  # Sample rate (optional, for audio files)
    channels: str | None  # Number of audio channels (optional, for audio files)


def get_media_file_info(file_path) -> MediaFileInfo:
    # Get the MIME type of the file
    mime_type, _ = mimetypes.guess_type(file_path)
    if not Path(file_path).exists():
        logger.error(f"{file_path} does not exists.")
        raise ValidationError("File is not valid")
    # Run ffmpeg command to extract information about the file
    command = ["ffmpeg", "-i", file_path]
    result = subprocess.run(command, capture_output=True, text=True)

    # Extract stderr output (because ffmpeg prints info to stderr)
    output = result.stderr

    # Initialize the dictionary to store extracted info
    file_info = {
        "mime_type": mime_type,
        "duration": "00:00:00.000",
        "duration_obj": timedelta(seconds=0),  # Default timedelta
    }
    # Extracting duration as a string
    duration_match = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", output)
    if duration_match:
        hours, minutes, seconds = map(float, duration_match.groups())
        # Store duration as string
        file_info["duration"] = f"{int(hours):02}:{int(minutes):02}:{seconds:06.3f}"
        # Convert duration to timedelta
        file_info["duration_obj"] = timedelta(
            hours=hours, minutes=minutes, seconds=seconds
        )

    # Extracting video-specific info if it’s a video file
    if mime_type and mime_type.startswith("video"):
        video_stream_match = re.search(r"Stream.*Video:\s+(\w+)", output)
        if video_stream_match:
            file_info["video_codec"] = video_stream_match.group(1)

        # Extracting resolution
        resolution_match = re.search(r"(\d+x\d+)", output)
        if resolution_match:
            file_info["resolution"] = resolution_match.group(1)

        # Extracting frame rate
        frame_rate_match = re.search(r"(\d+\.\d+)\s+fps", output)
        if frame_rate_match:
            file_info["frame_rate"] = frame_rate_match.group(1)

    # Extracting audio-specific info if it’s an audio or video file
    if mime_type and (mime_type.startswith("audio") or mime_type.startswith("video")):
        audio_codec_match = re.search(r"Stream.*Audio:\s+(\w+)", output)
        if audio_codec_match:
            file_info["audio_codec"] = audio_codec_match.group(1)

        # Extracting bitrate
        bitrate_match = re.search(r"bitrate:\s+(\d+\s+\w+)", output)
        if bitrate_match:
            file_info["bitrate"] = bitrate_match.group(1)

        # Extracting sample rate (for audio)
        sample_rate_match = re.search(r"(\d+)\s+Hz", output)
        if sample_rate_match:
            file_info["sample_rate"] = sample_rate_match.group(1)

        # Extracting channel information (for audio)
        channels_match = re.search(r",\s*(\d+)\s+channels", output)
        if channels_match:
            file_info["channels"] = channels_match.group(1)

    return file_info


def handle_uploaded_file(
    file: TemporaryUploadedFile | InMemoryUploadedFile,
) -> MediaFileInfo:
    """
    This function takes either a TemporaryUploadedFile or InMemoryUploadedFile,
    retrieves the file path, and calls get_media_file_info to return metadata.
    """
    media_info = {}
    # Check if the file is a TemporaryUploadedFile (it has a physical path)
    if isinstance(file, TemporaryUploadedFile):
        # File path is already available
        file_path = file.temporary_file_path()
        media_info = get_media_file_info(file_path)

    # Check if the file is an InMemoryUploadedFile (we need to write it to disk temporarily)
    elif isinstance(file, InMemoryUploadedFile):
        # Create a temporary directory using tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary file path within the temporary directory
            temp_file_path = os.path.join(temp_dir, file.name)

            # Write the InMemoryUploadedFile to the temporary file
            with open(temp_file_path, "wb") as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

            # File path is now available
            file_path = temp_file_path
            media_info = get_media_file_info(file_path)

    else:
        # Raise a validation error if the file type is unsupported
        raise ValidationError(
            "Unsupported file type. Please provide a TemporaryUploadedFile or InMemoryUploadedFile."
        )

    # Now call get_media_file_info with the file path
    file.seek(0)
    return media_info


def get_frontend_base_url(
    link_type: Literal["main", "demo"] = "main",
    path: str = "",
    service: Literal["payment", "iam", "learn", "notify", "media"] = "iam",
) -> str:
    """Function to construct the frontend url

    Args:
        link_type (Literal[&quot;main&quot;,&quot;demo&quot;], optional): _description_. Defaults to "main".
        path (str, optional): _description_. Defaults to "".

    Returns:
        str: _description_
    """
    base_url = get_base_url(service=service)
    enviroment = "local"
    if base_url.startswith(
        "https://dev-117782726-api.learngual.com"
    ) or base_url.startswith("http://dev-117782726-api.learngual.com"):
        enviroment = "staging"
    elif base_url.startswith("https://api.learngual.com") or base_url.startswith(
        "http://api.learngual.com"
    ):
        enviroment = "main"
    match (enviroment, link_type):
        case ("staging", "main"):
            return f"https://559staging.learngual.com/{path.lstrip('/')}"
        case ("main", "main"):
            return f"https://learngual.com/{path.lstrip('/')}"
        case ("main", "demo"):
            return f"https://demo.learngual.com/{path.lstrip('/')}"
        case ("staging", "demo"):
            return f"https://demo-test-01.learngual.com/{path.lstrip('/')}"
        case ("local", "demo"):
            return f"https://demo-test-01.learngual.com/{path.lstrip('/')}"
        case _:
            return f"https://559staging.learngual.com/{path.lstrip('/')}"


class FilterAndSearchManager:
    def __init__(
        self,
        *,
        request: HttpRequest,
        filterset_fields: list[str] | dict = [],
        filterset_keys: dict[str, Callable[[Any], Any | None]] = {},
        search_fields: list[str] = [],
        ordering_fields: list[str] = [],
        ordering: list[str] = [],
        filter_map: dict[str, str | list[str]] = dict(),
    ) -> None:
        """filter, ordering and search management class

        Args:
            request (HttpRequest): django request object
            filterset_fields (list[str], optional): a list of fields in the queryset
            to used and perform filters. Defaults to [].
            filterset_keys (dict[str,Callable[[Any],Any|None]], optional): \
                a dict of field_name:converter queryset in the queryset. Defaults to {
                "rating":int,
                "price":float
            }.
            search_fields (list[str], optional): fields to used for search. Defaults to [].
            ordering_fields (list[str], optional): fileds to use for default ordering
            when ordering is not specified. Defaults to [].
            ordering (list[str], optional): fields allowed to be used for ordering when
            specifying ordering in the request object. Defaults to [].
            filter_map (dict[str,str | list[str]], optional): a dictionary where the key is
              the query params key in the request and the value is the key that will be
              used for the filter. Defaults to dict().

        Examples:
            filter_map: {
                "courses":[
                    "student_teams__courses__id",
                    "instructor_teams__courses__id",
                ],
                "owner":"courses__owner__id",
                "rating[]":"courses__rating",
            }
        """

        self.filterset_fields = filterset_fields
        self.search_fields = search_fields
        self.ordering_fields = ordering_fields
        self.ordering = ordering
        self.request = request
        self.filter_map = filter_map
        self.filterset_keys = filterset_keys

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def subpress_error(
        self, function: Callable[[Any], Any | None], value: Any
    ) -> Any | None:
        try:
            return function(value)
        except (ValueError, TypeError):
            # Ignore errors raised during conversion and continue to the next field.
            pass

    def build_filter_params(
        self,
        request: HttpRequest,
        field_callable_dict: dict[
            str, Callable[[Any], Any] | list[Callable[[Any], Any]]
        ],
    ) -> dict[str, Any]:
        """
        Build filter parameters for Django queryset filter function from request data.

        Parameters:
            request (django.http.HttpRequest): The Django request object containing the data.
            field_callable_dict (dict[str, Callable[[Any], Any]|list[Callable[[Any], Any]]]):\
                 A dictionary with field names as keys and callables as values.

        Returns:
            dict: A dictionary of filter parameters to be used with Django queryset .filter() function.
        """
        filter_params = {}

        if not isinstance(request.GET, QueryDict):
            return filter_params

        for field, field_callable in field_callable_dict.items():
            if isinstance(field_callable, list) and len(field_callable) > 0:
                # If the field_callable is specified as a list, apply each converter to the list of values.
                values = request.GET.getlist(field)
                converted_values = [
                    self.subpress_error(callable_item, val)
                    for val, callable_item in zip(values, field_callable)
                ]
                # Filter out None and empty values from the converted list.
                converted_values = [val for val in converted_values if val is not None]
                if converted_values:
                    filter_params[field] = converted_values
            else:
                # If the field_callable is not a list, apply the converter to the single value.
                value = request.GET.get(field)
                if value is not None:
                    try:
                        converted_value = field_callable(value)
                        if converted_value is not None:
                            filter_params[field] = converted_value
                    except (ValueError, TypeError):
                        # Ignore errors raised during conversion and continue to the next field.
                        pass

        return filter_params

    def filter_queryset_with_filterset_keys(self, queryset: QuerySet) -> QuerySet:
        """method take in a queryset and filter it based on the mapping that was provided
        with filterset_keys

        filterset_keys:
        {
            "name":str,
            "age":int, #this retrieve it as a single value
            "ids":[str] #this try retriving the query params as a list
        }

        Args:
            queryset (QuerySet):

        Returns:
            QuerySet:
        """
        if not self.filterset_keys:
            return queryset

        kwargs = self.build_filter_params(self.request, self.filterset_keys)
        if kwargs:
            queryset = queryset.filter(**kwargs)

        return queryset

    def filter_queryset_with_dict_maping(self, queryset: QuerySet) -> QuerySet:
        """method take in a queryset and filter it based on the mapping that was provided

        Args:
            queryset (QuerySet):

        Returns:
            QuerySet:
        """
        if not self.filter_map:
            return queryset

        query_params: QueryDict = self.request.GET  # get query dictionary
        query_kwargs = dict()
        for key, value in self.filter_map.items():  # loop through the filter map
            if key in query_params.dict():  # if the filter map key exists
                if type(value) == str:  # check if it is string
                    data_list = query_params.getlist(key)
                    data_single = query_params.get(key)
                    if data_list:
                        query_kwargs[f"{value}__in"] = data_list
                    elif data_single:
                        query_kwargs[value] = data_single
                elif type(value) == list:
                    q = Q()
                    data_list = query_params.getlist(key)
                    data_single = query_params.get(key)

                    if data_list:
                        for sub_value in value:
                            q |= Q(**{f"{sub_value}__in": data_list})
                        queryset = queryset.filter(q)
                    elif data_single:
                        query_kwargs[value] = query_params.get(key)
                        for sub_value in value:
                            q |= Q(**{sub_value: data_single})
                        queryset = queryset.filter(q)
        if query_kwargs:
            queryset = queryset.filter(**query_kwargs)

        return queryset

    def filter_queryset(self, queryset: models.QuerySet) -> models.QuerySet:
        """
        Given a queryset, filter it with whichever filter backend is in use.

        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        for Backend in list(self.filter_backends):
            backend: DjangoFilterBackend = Backend()
            queryset = backend.filter_queryset(self.request, queryset, self)
        queryset = self.filter_queryset_with_dict_maping(queryset)
        queryset = self.filter_queryset_with_filterset_keys(queryset)
        return queryset


class DecodedJWTToken(TypedDict, total=False):
    exp: str
    iat: str
    nbf: str
    orig_iat: str
    iss: str
    sub: str
    aud: str
    jti: str
    typ: str
    # Allow additional claims
    # TypedDict allows extra keys by default when total=False


def decode_jwt_access_token(token) -> DecodedJWTToken:
    # Decode the JWT access token
    decoded_token = jwt.decode(token, options={"verify_signature": False})

    # Convert timestamp values to timedelta objects
    if "exp" in decoded_token:
        decoded_token["exp"] = datetime.fromtimestamp(decoded_token["exp"]).isoformat()

    if "iat" in decoded_token:
        decoded_token["iat"] = datetime.fromtimestamp(decoded_token["iat"]).isoformat()
    if "nbf" in decoded_token:
        decoded_token["nbf"] = datetime.fromtimestamp(decoded_token["nbf"]).isoformat()
    if "orig_iat" in decoded_token:
        decoded_token["orig_iat"] = datetime.fromtimestamp(
            decoded_token["orig_iat"]
        ).isoformat()

    return decoded_token


class JSONFieldEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        return super().default(obj)
