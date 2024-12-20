from django.apps import AppConfig


class WebportalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "webportal"

    def ready(self):
        import webportal.signals
