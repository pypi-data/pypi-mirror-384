from logging import getLogger

from django.apps import AppConfig

log = getLogger(__name__)


class BiasedDjangoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "biased.django"
    label = "biased_django"
