from rest_framework import status
from rest_framework.exceptions import APIException


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Service temporarily unavailable, try again later."
    default_code = "service_unavailable"


class Forbidden(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "forbidden"
    default_code = "forbidden"


class Badrequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "bad request payload"
    default_code = "bad_request"


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "not acceptable"
    default_code = "not_acceptable"


class MethodNotAllowed(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = "not allow"
    default_code = "not_allowed"


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "not found"
    default_code = "not_found"


class Redirect(APIException):
    status_code = status.HTTP_307_TEMPORARY_REDIRECT
    default_detail = "redirect"
    default_code = "redirect"


class UnAuthorized(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "unauthorized"
    default_code = "unauthorized"


class UnAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "unauthorized"
    default_code = "unauthorized"


class ProxyAuthenticationRequired(APIException):
    status_code = status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED
    default_detail = "proxy authentication required"
    default_code = "proxy_authentication_required"


class ValidationError(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "validation error"
    default_code = "validation_error"
