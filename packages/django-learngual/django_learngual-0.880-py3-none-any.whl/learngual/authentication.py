import importlib
import logging
import os
import urllib.parse
from logging import getLogger

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http.request import HttpRequest
from django.utils import timezone, translation
from rest_framework.request import Request
from rest_framework_simplejwt import authentication
from rest_framework_simplejwt.exceptions import InvalidToken

from . import custom_exceptions
from .translator import translate as _
from .utils import decode_jwt_access_token, get_language_code

logger = getLogger(__file__)

User = get_user_model()

LEARNGUAL_SERVICE_API_KEY = getattr(
    settings, "LEARNGUAL_SERVICE_API_KEY", None
) or os.getenv("LEARNGUAL_SERVICE_API_KEY", None)

"""
Configure authentication class
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        ...
        "iam_service.users.authentication.LearngualAuthentication",
        ...
    ),
    ...
}

LEARNGUAL_AUTH_RETRIEVE_URL=<auth server url to authenticate if user is login>
LEARNGUAL_AUTH_TEST_MODE=<True or False used for testing provide dummy data to authenticate user>
LEARNGUAL_AUTH_GET_USER=<dot path to the callable >

Data = {
    "account": {
        "id": "84bcaf2972",
        "cover_photo": None,
        "profile_photo": None,
        "type": "PERSONNAL",
        "metadata": {},
        "created_at": "2023-01-13T16:33:52.084540Z",
        "updated_at": "2023-01-13T16:33:52.084576Z"
    },
    "email": "Bulah53@gmail.com",
    "first_name": "Caitlyn",
    "id": "40e0e7013f",
    "last_name": "Marquardt",
    "registration_step": "REGISTRATION_COMPLETED",
    "username": "Eloisa.Senger42"
}

def get_user(data:Data):

    print("data in get user")
    return get_user_model().objects.get_or_create()

"""


user_test_data = {
    "account": {
        "id": "84bcaf2972",
        "cover_photo": None,
        "profile_photo": None,
        "type": "PERSONAL",
        "metadata": {},
        "created_at": "2023-01-13T16:33:52.084540Z",
        "updated_at": "2023-01-13T16:33:52.084576Z",
    },
    "email": "Bulah53@gmail.com",
    "first_name": "Caitlyn",
    "id": "40e0e7013f",
    "last_name": "Marquardt",
    "registration_step": "REGISTRATION_COMPLETED",
    "username": "Eloisa.Senger42",
}


def load_callable(path: str) -> object | None:
    paths = path.split(".")
    modules = importlib.import_module(".".join(paths[:-1]))
    result = getattr(modules, paths[-1], None)
    if not result:
        logger.warning("Module does no exists. path: %s", path)
    return result


LEARNGUAL_AUTH_RETRIEVE_URL = getattr(settings, "LEARNGUAL_AUTH_RETRIEVE_URL", None)
LEARNGUAL_AUTH_GET_USER = getattr(settings, "LEARNGUAL_AUTH_GET_USER", None)
LEARNGUAL_AUTH_ACCOUNT_MODEL_PATH = getattr(
    settings, "LEARNGUAL_AUTH_ACCOUNT_MODEL_PATH", None
)


assert (
    LEARNGUAL_AUTH_RETRIEVE_URL
), "LEARNGUAL_AUTH_RETRIEVE_URL must be provided in the settings."
assert (
    LEARNGUAL_AUTH_GET_USER
), "LEARNGUAL_AUTH_GET_USER must be provided in the settings."


get_user: callable = load_callable(LEARNGUAL_AUTH_GET_USER)
assert get_user, "No callable exists in path:%s" % LEARNGUAL_AUTH_GET_USER


class AuthenticationBaseHelper:
    @classmethod
    def get_http_headers(cls, request: Request | HttpRequest):
        headers = {
            key.lower().lstrip("http_"): value
            for key, value in request.META.items()
            if key.lower().startswith("http_")
        }
        return headers

    @classmethod
    def get_query_str(cls, request: Request | HttpRequest):
        return "?{query}".format(query=request.META.get("QUERY_STRING", ""))

    def authenticate_service(self, request: Request | HttpRequest):
        headers = self.get_header(request)

        if service_key := headers.get("service_key"):
            logger.info("authentication send with service account")
            if service_key == LEARNGUAL_SERVICE_API_KEY:
                service_user = User(id="service", username="service")
                service_user.is_service = True
                return service_user, service_key
            logger.warning("invalid service key")
            msg = _("Invalid service key")
            raise custom_exceptions.UnAuthenticated(msg)

    def get_user(self, validated_token, headers):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[authentication.api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        res_data = {}
        res_data["id"] = user_id
        if account_id := headers.get("account_id"):
            res_data["account"] = {"id": account_id}
        user = get_user(res_data)
        account = getattr(user, "account", None)
        if account and account.owner != user:
            logger.warning(f"{account = }, {account.owner = }, request user {user}")
            raise custom_exceptions.UnAuthenticated(_("Invalid account provided"))
        return user

    def get_raw_token(self, header):
        """
        Extracts an unvalidated JSON web token from the given "Authorization"
        header value.
        """
        parts = header.split()

        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if str(parts[0]).lower().strip() != "bearer":
            # Assume the header does not contain a JSON web token
            return None

        if len(parts) != 2:
            raise custom_exceptions.UnAuthenticated(
                _("Authorization header must contain two space-delimited values"),
                code="bad_authorization_header",
            )

        return parts[1]

    def append_bearer(self, token: str):
        if (
            token
            and isinstance(token, str)
            and not token.lower().strip().startswith("bearer")
        ):
            return "Bearer " + token
        return token

    def get_header(self, request: Request | HttpRequest):
        """
        Extracts the header containing the JSON web token from the given
        request.
        """
        account_id = str(
            request.META.get("HTTP_ACCOUNT", "")
            or request.META.get("HTTP_X_ACCOUNT", "")
            or request.COOKIES.get("x-account", "")
            or request.COOKIES.get("account", "")
            or request.COOKIES.get("_account", "")
            or request.GET.get("x-account")
            or request.GET.get("_account")
            or ""
        )
        api_key = str(
            request.META.get("HTTP_API_KEY", "")
            or request.META.get("HTTP_X_API_KEY", "")
            or request.COOKIES.get("x-api-key", "")
            or request.COOKIES.get("api-key", "")
            or request.GET.get("x-api-key")
            or request.GET.get("api-key")
            or ""
        )
        service_key = str(
            request.META.get("HTTP_SERVICE_KEY", "")
            or request.META.get("HTTP_X_SERVICE_KEY", "")
            or request.COOKIES.get("x-service-key", "")
            or request.COOKIES.get("service-key", "")
            or request.GET.get("service-key", "")
            or request.GET.get("_service-key", "")
            or ""
        )
        authorization = str(
            request.META.get("HTTP_AUTHORIZATION", "")
            or request.COOKIES.get("x-authorization", "")
            or request.COOKIES.get("authorization", "")
            or request.COOKIES.get("x-token", "")
            or request.COOKIES.get("token", "")
            or request.GET.get("token", "")
            or request.GET.get("_token", "")
            or ""
        )

        return dict(
            account_id=urllib.parse.unquote(account_id or ""),
            api_key=urllib.parse.unquote(api_key or ""),
            authorization=urllib.parse.unquote(self.append_bearer(authorization or "")),
            service_key=urllib.parse.unquote(service_key or ""),
        )


class LearngualAuthentication(
    AuthenticationBaseHelper, authentication.JWTAuthentication
):
    """
    An authentication plugin that authenticates requests through a JSON web
    token provided in a request header.
    """

    def authenticate_api_key(self, request: Request | HttpRequest):
        header = self.get_header(request)
        if not (api_key := header.get("api_key")):
            return
        headers = self.get_http_headers(request)
        query_str = self.get_query_str(request)
        res = requests.get(LEARNGUAL_AUTH_RETRIEVE_URL + query_str, headers=headers)
        if not res.ok:
            logging.warning(
                "request to IAM service did not go through: %s", res.content
            )
            if res.status_code == 401:
                raise custom_exceptions.UnAuthenticated(_("Invalid API key."))
            raise custom_exceptions.UnAuthenticated(_("Service is down."))
        res_data = res.json()
        if not (user := get_user(res_data)):
            return
        self.set_language(user, request)
        return (user, api_key)

    def authenticate(self, request: Request | HttpRequest):
        if is_service := self.authenticate_service(request):
            return is_service
        if is_api := self.authenticate_api_key(request):
            return is_api
        header = self.get_header(request)
        if not (authorization := header.get("authorization")):
            return
        raw_token = self.get_raw_token(authorization)
        if raw_token is None:
            return
        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken as e:
            raise custom_exceptions.UnAuthorized(*e.args)
        data = decode_jwt_access_token(str(validated_token))
        jti = data.get("jti")
        anonymous_id = data.get("anonymous_id", None)
        if jti and cache.get(jti):
            raise custom_exceptions.UnAuthorized(_("Token blacklisted"))

        if not (user := self.get_user(validated_token, header)):
            return

        if user and user.token_blacklist_at:
            created_at: str = data.get("created_at")
            if (
                not created_at
                or timezone.datetime.fromisoformat(created_at.rstrip("zZ"))
                <= user.token_blacklist_at
            ):
                raise custom_exceptions.UnAuthorized(_("Token blacklisted"))
        self.set_language(user, request)
        if (
            user
            and anonymous_id
            and (update_anonymous_link := getattr(user, "update_anonymous_link", None))
        ):
            if callable(update_anonymous_link):
                update_anonymous_link(anonymous_id)
            else:
                raise custom_exceptions.UnAuthenticated(_("Invalid anonymous user"))
        return user, validated_token

    def set_language(self, user, request: Request | HttpRequest):
        if user and not request.GET.get("_lang"):
            if account := getattr(user, "account", None):
                translation.activate(get_language_code(account.language))
            else:
                translation.activate(get_language_code(user.language))
