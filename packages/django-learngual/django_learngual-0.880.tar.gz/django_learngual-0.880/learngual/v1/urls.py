from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()


# router.register("accounts", views.AccountViewSet, basename="accounts")


app_name = "learngual_v1"
urlpatterns = router.urls
