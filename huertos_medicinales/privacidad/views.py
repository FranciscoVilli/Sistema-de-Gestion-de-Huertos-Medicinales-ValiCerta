from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core import signing
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from .forms import RespuestaForm
from .forms import SolicitudForm
from .models import PreferenciaCookies
from .models import SolicitudDerecho
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


@login_required
@require_http_methods(["GET", "POST"])
def derechos(request):
    form = SolicitudForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.usuario = request.user
        item.save()
        messages.success(
            request,
            (
                "Solicitud registrada. Puedes consultar su estado y "
                "respuesta aquí. No se ha enviado un correo "
                "automáticamente."
            ),
        )
        return redirect("privacidad:solicitud", pk=item.pk)
    page = Paginator(
        SolicitudDerecho.objects.filter(usuario=request.user),
        10,
    ).get_page(request.GET.get("page"))
    return render(request, "privacidad/derechos.html", {"form": form, "page": page})


@login_required
def solicitud(request, pk):
    item = get_object_or_404(SolicitudDerecho, pk=pk, usuario=request.user)
    return render(request, "privacidad/solicitud.html", {"solicitud": item})


@login_required
@permission_required("privacidad.gestionar_derechos", raise_exception=True)
def gestion(request):
    page = Paginator(SolicitudDerecho.objects.select_related("usuario"), 20).get_page(
        request.GET.get("page"),
    )
    return render(request, "privacidad/gestion.html", {"page": page})


@login_required
@permission_required("privacidad.gestionar_derechos", raise_exception=True)
@require_http_methods(["GET", "POST"])
def responder(request, pk):
    item = get_object_or_404(SolicitudDerecho, pk=pk)
    form = RespuestaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        response = form.save(commit=False)
        response.solicitud = item
        response.gestor = request.user
        response.save()
        messages.success(request, "Respuesta registrada y disponible para el titular.")
        return redirect("privacidad:responder", pk=pk)
    return render(
        request,
        "privacidad/responder.html",
        {"form": form, "solicitud": item},
    )
