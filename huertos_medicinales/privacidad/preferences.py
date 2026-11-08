from django.conf import settings
from django.core import signing

COOKIE_NAME = "huertos_privacidad"
COOKIE_MAX_AGE = 180 * 24 * 60 * 60
VERSION = "2026-10-21"
SALT = "huertos.privacidad.v1"


def preferencia(request):
    try:
        data = request.get_signed_cookie(COOKIE_NAME, salt=SALT, max_age=COOKIE_MAX_AGE)
        value = signing.loads(data, salt=SALT, max_age=COOKIE_MAX_AGE)
        if value.get("version") == VERSION and isinstance(value.get("mapas"), bool):
            return value
    except KeyError, signing.BadSignature, TypeError, AttributeError:
        pass
    return None


def contexto(request):
    choice = preferencia(request)
    return {
        "cookies_elegidas": choice is not None,
        "mapas_permitidos": bool(choice and choice["mapas"]),
        "legal_version": VERSION,
        "legal_profile": settings.LEGAL_PROFILE,
        "session_cookie_name": settings.SESSION_COOKIE_NAME,
        "csrf_cookie_name": settings.CSRF_COOKIE_NAME,
        "session_days": settings.SESSION_COOKIE_AGE // 86400,
        "csrf_days": settings.CSRF_COOKIE_AGE // 86400,
    }
