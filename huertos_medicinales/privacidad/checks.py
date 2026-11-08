from django.conf import settings
from django.core.checks import Error
from django.core.checks import Tags
from django.core.checks import register


@register(Tags.security, deploy=True)
def legal_production_check(app_configs, **kwargs):
    profile = settings.LEGAL_PROFILE
    needed = [
        "razon_social",
        "email",
        "telefono",
        "domicilio",
        "bases",
        "conservacion",
        "proveedores",
    ]
    missing = [name for name in needed if not profile.get(name)]
    if (
        profile.get("datos_prueba")
        or missing
        or not profile.get("aprobado")
        or str(profile.get("email", "")).endswith(".invalid")
    ):
        return [
            Error(
                (
                    "La información legal contiene datos de prueba o está "
                    "incompleta. Confirma identidad, contacto, bases, "
                    "conservación y proveedores antes de publicar."
                ),
                id="privacidad.E001",
            ),
        ]
    return []
