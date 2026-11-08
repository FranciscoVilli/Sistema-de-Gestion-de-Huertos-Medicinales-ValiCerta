from http import HTTPStatus

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from .admin import ComunidadAdmin
from .models import Comunidad
from .models import EventoComunidad

pytestmark = pytest.mark.django_db


@pytest.fixture
def usuario(django_user_model):
    return django_user_model.objects.create_user(email="comunidad@example.com")


def payload():
    return {
        "nombre": "Huerto comunitario",
        "provincia": "Pichincha",
        "localidad": "Quito",
        "descripcion": "Aprendizaje compartido",
        "encuentro": "Consultar el punto comunitario",
        "latitud": "-0.18",
        "longitud": "-78.47",
        "confirmar_publicacion": "on",
        "estado": "publicada",
    }


def test_solicitud_no_se_publica_por_manipular_formulario(client, usuario):
    client.force_login(usuario)
    assert (
        client.post(reverse("comunidades:crear"), payload()).status_code
        == HTTPStatus.FOUND
    )
    comunidad = Comunidad.objects.get()
    assert comunidad.estado == "pendiente"
    assert EventoComunidad.objects.get().accion == "solicitud"
    client.logout()
    assert (
        client.get(reverse("comunidades:detalle", args=[comunidad.pk])).status_code
        == HTTPStatus.NOT_FOUND
    )
    assert (
        "Huerto comunitario"
        not in client.get(reverse("comunidades:listado")).content.decode()
    )


def test_publicacion_revisada_muestra_mapa_y_retiro_lo_oculta(client, usuario, rf):
    client.force_login(usuario)
    client.post(reverse("comunidades:crear"), payload())
    comunidad = Comunidad.objects.get()
    request = rf.post("/")
    request.user = usuario
    model_admin = ComunidadAdmin(Comunidad, AdminSite())
    model_admin.message_user = lambda *args, **kwargs: None
    model_admin.publicar(request, Comunidad.objects.all())
    comunidad.refresh_from_db()
    assert comunidad.estado == "publicada"
    assert comunidad.eventos.filter(accion="publicada").exists()
    client.logout()
    response = client.get(reverse("comunidades:detalle", args=[comunidad.pk]))
    assert response.status_code == HTTPStatus.OK
    assert "openstreetmap.org/export/embed.html" not in response.content.decode()
    client.post(reverse("privacidad:guardar_cookies"), {"eleccion": "mapas"})
    response = client.get(reverse("comunidades:detalle", args=[comunidad.pk]))
    assert "openstreetmap.org/export/embed.html" in response.content.decode()
    assert "comunidad@example.com" not in response.content.decode()
    client.force_login(usuario)
    client.post(reverse("comunidades:retirar", args=[comunidad.pk]))
    client.logout()
    assert (
        client.get(reverse("comunidades:detalle", args=[comunidad.pk])).status_code
        == HTTPStatus.NOT_FOUND
    )


def test_sin_confirmacion_o_coordenadas_validas_no_hay_solicitud(client, usuario):
    client.force_login(usuario)
    for overrides in [
        {"confirmar_publicacion": ""},
        {"latitud": "91"},
        {"latitud": "-0.123456"},
    ]:
        assert (
            client.post(
                reverse("comunidades:crear"),
                {**payload(), **overrides},
            ).status_code
            == HTTPStatus.OK
        )
    assert not Comunidad.objects.exists()


def test_mapa_agregado_respeta_consentimiento_y_estado(client, usuario, rf):
    client.force_login(usuario)
    client.post(
        reverse("comunidades:crear"),
        {**payload(), "plantas_destacadas": "menta"},
    )
    comunidad = Comunidad.objects.get()
    request = rf.post("/")
    request.user = usuario
    model_admin = ComunidadAdmin(Comunidad, AdminSite())
    model_admin.message_user = lambda *args, **kwargs: None
    model_admin.publicar(request, Comunidad.objects.all())
    client.logout()

    response = client.get(reverse("comunidades:iniciativas"))
    content = response.content.decode()
    assert "mapa-comunidades-datos" not in content
    assert "vendor/leaflet/leaflet.js" not in content

    client.post(reverse("privacidad:guardar_cookies"), {"eleccion": "mapas"})
    response = client.get(reverse("comunidades:iniciativas"))
    content = response.content.decode()
    assert "mapa-comunidades-datos" in content
    assert "vendor/leaflet/leaflet.js" in content
    assert "Huerto comunitario" in content
    assert "menta" in content

    client.force_login(usuario)
    client.post(reverse("comunidades:retirar", args=[comunidad.pk]))
    client.logout()
    response = client.get(reverse("comunidades:iniciativas"))
    assert "Huerto comunitario" not in response.content.decode()


def test_no_responsable_no_puede_retirar(client, usuario, django_user_model):
    client.force_login(usuario)
    client.post(reverse("comunidades:crear"), payload())
    comunidad = Comunidad.objects.get()
    client.force_login(django_user_model.objects.create_user(email="otro@example.com"))
    assert (
        client.post(reverse("comunidades:retirar", args=[comunidad.pk])).status_code
        == HTTPStatus.NOT_FOUND
    )


def test_publicacion_requiere_permiso_explicito(usuario, rf):
    request = rf.get("/")
    request.user = usuario
    assert not ComunidadAdmin(Comunidad, AdminSite()).has_publish_permission(request)
