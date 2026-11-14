from http import HTTPStatus

import pytest
from django.conf import settings
from django.core import signing
from django.http import HttpResponse
from django.test import Client
from django.test import RequestFactory
from django.test import override_settings
from django.urls import reverse

from huertos_medicinales.comunidades.models import Comunidad
from huertos_medicinales.users.forms import UserSignupForm

from .checks import legal_production_check
from .models import AceptacionCondiciones
from .models import PreferenciaCookies
from .preferences import COOKIE_MAX_AGE
from .preferences import COOKIE_NAME
from .preferences import SALT
from .preferences import VERSION
from .preferences import preferencia

pytestmark = pytest.mark.django_db


@pytest.fixture
def usuario(django_user_model):
    return django_user_model.objects.create_user(email="privacidad@example.com")


@pytest.fixture
def comunidad(usuario):
    return Comunidad.objects.create(
        responsable=usuario,
        nombre="Huerto",
        provincia="Pichincha",
        localidad="Quito",
        descripcion="Cultivo",
        encuentro="Punto comunitario",
        latitud="-0.18",
        longitud="-78.47",
        estado="publicada",
    )


def test_mapas_no_se_cargan_sin_autorizacion(client, comunidad):
    response = client.get(reverse("comunidades:detalle", args=[comunidad.pk]))
    assert response.status_code == HTTPStatus.OK
    assert "<iframe" not in response.content.decode()
    assert "Permitir y cargar mapa" in response.content.decode()
    assert not PreferenciaCookies.objects.exists()


def test_rechazo_autorizacion_y_retirada_son_reales(client, comunidad):
    url = reverse("privacidad:guardar_cookies")
    for choice, enabled in [
        ("necesarias", False),
        ("mapas", True),
        ("necesarias", False),
    ]:
        response = client.post(
            url,
            {"eleccion": choice, "next": reverse("privacidad:cookies")},
        )
        assert response.status_code == HTTPStatus.FOUND
        cookie = response.cookies[COOKIE_NAME]
        assert cookie["httponly"]
        assert cookie["samesite"] == "Lax"
        assert cookie["max-age"] == COOKIE_MAX_AGE
        html = client.get(
            reverse("comunidades:detalle", args=[comunidad.pk]),
        ).content.decode()
        assert ("<iframe" in html) is enabled
        assert PreferenciaCookies.objects.first().mapas_externos is enabled
    assert PreferenciaCookies.objects.count() == len(["rechazo", "permiso", "retirada"])


def test_cookie_manipulada_o_version_antigua_no_habilita_mapas(client, comunidad):
    client.cookies[COOKIE_NAME] = "true"
    assert (
        "<iframe"
        not in client.get(
            reverse("comunidades:detalle", args=[comunidad.pk]),
        ).content.decode()
    )
    payload = signing.dumps({"version": "vieja", "mapas": True}, salt=SALT)
    response = client.post(reverse("privacidad:guardar_cookies"), {"eleccion": "mapas"})
    client.cookies[COOKIE_NAME] = response.cookies[COOKIE_NAME].value[:-1] + "x"
    assert (
        "<iframe"
        not in client.get(
            reverse("comunidades:detalle", args=[comunidad.pk]),
        ).content.decode()
    )
    request = RequestFactory().get("/")
    request.COOKIES[COOKIE_NAME] = "invalida"
    assert preferencia(request) is None
    old = HttpResponse()
    old.set_signed_cookie(COOKIE_NAME, payload, salt=SALT)
    client.cookies[COOKIE_NAME] = old.cookies[COOKIE_NAME].value
    assert (
        "<iframe"
        not in client.get(
            reverse("comunidades:detalle", args=[comunidad.pk]),
        ).content.decode()
    )


def test_preferencias_no_permiten_redireccion_externa_y_requieren_csrf(client):
    response = client.post(
        reverse("privacidad:guardar_cookies"),
        {"eleccion": "necesarias", "next": "https://otro.example/"},
    )
    assert response.url == "/"
    assert (
        Client(enforce_csrf_checks=True)
        .post(reverse("privacidad:guardar_cookies"), {"eleccion": "mapas"})
        .status_code
        == HTTPStatus.FORBIDDEN
    )


def test_condiciones_no_aceptadas_impiden_registro():
    form = UserSignupForm(
        data={
            "email": "nuevo@example.com",
            "password1": "Clave-prueba-9843!",
            "password2": "Clave-prueba-9843!",
        },
    )
    assert not form.is_valid()
    assert "aceptar_condiciones" in form.errors


def test_no_hay_aprobacion_legal_ficticia():
    assert any(error.id == "privacidad.E001" for error in legal_production_check(None))
    profile = {
        **settings.LEGAL_PROFILE,
        "datos_prueba": False,
        "aprobado": True,
        **dict.fromkeys(
            [
                "razon_social",
                "email",
                "telefono",
                "domicilio",
                "bases",
                "conservacion",
                "proveedores",
            ],
            "Confirmado para test",
        ),
    }
    with override_settings(LEGAL_PROFILE=profile):
        assert not legal_production_check(None)


def test_identidad_y_avisos_son_publicos(client):
    for route in ["aviso", "cookies", "condiciones"]:
        response = client.get(reverse(f"privacidad:{route}"))
        assert response.status_code == HTTPStatus.OK
        assert "Huertos Medicinales" in response.content.decode()
        assert "site-footer" not in response.content.decode()
        assert 'class="sidebar"' not in response.content.decode()
        assert "cookies-ui.css" in response.content.decode()
        assert "Proyecto académico" not in response.content.decode()
        assert (
            "Datos legales de prueba" in response.content.decode() or route == "cookies"
        )


def test_registro_guarda_condiciones_sin_autorizar_mapas(client, django_user_model):
    response = client.post(
        reverse("account_signup"),
        {
            "email": "condiciones@example.com",
            "password1": "Clave-prueba-9843!",
            "password2": "Clave-prueba-9843!",
            "aceptar_condiciones": "on",
        },
    )
    assert response.status_code == HTTPStatus.FOUND
    user = django_user_model.objects.get(email="condiciones@example.com")
    assert AceptacionCondiciones.objects.get(usuario=user).version == VERSION
    assert COOKIE_NAME not in response.cookies
    assert not PreferenciaCookies.objects.filter(
        usuario=user, mapas_externos=True,
    ).exists()
