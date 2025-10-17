from logging import getLogger

from django.apps import AppConfig

log = getLogger(__name__)


class BiasedDjangoJsonformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "biased.django_jsonform"
    label = "biased_django_jsonform"
