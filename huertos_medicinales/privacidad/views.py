from django.core import signing
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import PreferenciaCookies
from .preferences import COOKIE_MAX_AGE
from .preferences import COOKIE_NAME
from .preferences import SALT
from .preferences import VERSION


@require_POST
def guardar_cookies(request):
    choice = request.POST.get("eleccion")
    if choice not in {"necesarias", "mapas"}:
        return redirect("privacidad:cookies")
    event = PreferenciaCookies.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        version=VERSION,
        mapas_externos=choice == "mapas",
    )
    target = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        target = "/"
    response = redirect(target)
    data = signing.dumps(
        {"version": VERSION, "mapas": event.mapas_externos, "registro": str(event.pk)},
        salt=SALT,
    )
    response.set_signed_cookie(
        COOKIE_NAME,
        data,
        salt=SALT,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=request.is_secure(),
        samesite="Lax",
    )
    return response
