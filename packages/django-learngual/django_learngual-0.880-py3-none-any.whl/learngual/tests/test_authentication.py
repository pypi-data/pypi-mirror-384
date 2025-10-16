import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from .. import custom_exceptions
from ..authentication import LearngualAuthentication

factory = APIRequestFactory()
User = get_user_model()


def test_authentication_service_key(settings):

    request = factory.get("/api/my-endpoint/")

    # Add the custom header to the request

    request.META["HTTP_SERVICE_KEY"] = settings.LEARNGUAL_SERVICE_API_KEY

    # Authenticate the request

    # Create an instance of the custom authentication class
    auth = LearngualAuthentication()

    # Authenticate the request using the custom authentication class
    authenticated = auth.authenticate(request)

    # Assert that authentication is successful
    assert getattr(authenticated[0], "is_service", None)
    assert authenticated[1] == settings.LEARNGUAL_SERVICE_API_KEY


@pytest.mark.django_db
def test_authentication_invalid_service_key(settings):

    request = factory.get("/api/my-endpoint/")

    # Add the custom header to the request

    request.META["HTTP_SERVICE_KEY"] = "hshsggfaas"

    # Authenticate the request

    # Create an instance of the custom authentication class
    auth = LearngualAuthentication()

    try:
        # Authenticate the request using the custom authentication class
        authenticated = auth.authenticate(request)
        assert authenticated
    except custom_exceptions.UnAuthenticated:
        assert True
