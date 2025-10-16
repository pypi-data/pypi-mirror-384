from django.urls import include, path

app_name = "learngual"

urlpatterns = [
    path("v1/", include("iam_service.learngual.v1.urls")),
]
