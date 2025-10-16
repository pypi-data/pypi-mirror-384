from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LearngualConfig(AppConfig):
    name = "learngual"
    verbose_name = _("Learngual")

    def ready(self):
        try:
            import learngual.signals  # noqa F401
            import learngual.schema  # noqa F401
        except ImportError:
            pass


class IAMLearngualConfig(AppConfig):
    name = "iam_service.learngual"
    verbose_name = _("Learngual")

    def ready(self):
        try:
            import iam_service.learngual.signals  # noqa F401
            import iam_service.learngual.schema  # noqa F401
        except ImportError:
            pass
