from django.apps import AppConfig


class PrivacidadConfig(AppConfig):
    name = "huertos_medicinales.privacidad"
    verbose_name = "Privacidad y derechos"

    def ready(self):
        from . import checks  # noqa: F401, PLC0415
