from http import HTTPStatus

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from .admin import ComunidadAdmin
from .community import public_name
from .models import Comunidad
from .models import EventoComunidad
from .models import PerfilComunitario

pytestmark = pytest.mark.django_db


@pytest.fixture
def usuario(django_user_model):
    return django_user_model.objects.create_user(
        email="comunidad@example.com",
        name="Cultivadora",
        fecha_nacimiento="1990-01-01",
        genero="otro",
        telefono="0990000000",
        direccion="Quito",
    )


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


def test_iniciativas_removed_and_rules_have_return(client, usuario):
    client.force_login(usuario)
    assert client.get("/comunidades/iniciativas/").status_code == 404
    for view in ("foro", "comunidades", "mapa"):
        response = client.get(reverse("comunidades:listado"), {"vista": view})
        assert response.status_code == 200
        assert "/comunidades/iniciativas/" not in response.content.decode()
    response = client.get(reverse("comunidades:reglas"))
    assert response.status_code == 200
    assert response.content.decode().count("Regresar al foro") == 2
    assert response.content.decode().count('class="rules-item"') == 5


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


def test_public_name_usa_el_nombre_de_cuenta_por_defecto(usuario, django_user_model):
    assert public_name(usuario) == "Cultivadora"
    sin_nombre = django_user_model.objects.create_user(email="sinnombre@example.com")
    assert public_name(sin_nombre) == f"Cultivador {sin_nombre.pk}"


def test_public_name_respeta_perfil_comunitario_visible_u_oculto(usuario):
    PerfilComunitario.objects.create(
        usuario=usuario,
        nombre="Jardinera Q",
        visible=True,
    )
    assert public_name(usuario) == "Jardinera Q"
    usuario.perfil_comunitario.visible = False
    usuario.perfil_comunitario.save()
    assert public_name(usuario) == f"Cultivador {usuario.pk}"
