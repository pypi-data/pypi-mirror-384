from django.apps import AppConfig


class SharedAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shared_auth"

    def ready(self):
        from . import models, exceptions