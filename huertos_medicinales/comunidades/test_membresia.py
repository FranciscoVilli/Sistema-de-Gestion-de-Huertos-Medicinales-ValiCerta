from datetime import date

import pytest
from django.urls import reverse

from .models import CertificacionTalento
from .models import Comunidad
from .models import Miembro

pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario(client, django_user_model):
    responsable = django_user_model.objects.create_user(
        email="responsable@example.com",
        name="Responsable",
        fecha_nacimiento=date(1990, 1, 1),
        genero="otro",
        telefono="0990000000",
        direccion="Ibarra",
    )
    voluntario = django_user_model.objects.create_user(
        email="voluntario@example.com",
        name="Voluntario",
        fecha_nacimiento=date(1990, 1, 1),
        genero="otro",
        telefono="0990000000",
        direccion="Ibarra",
    )
    comunidad = Comunidad.objects.create(
        responsable=responsable,
        nombre="Huerto Ibarra",
        provincia="Imbabura",
        localidad="Ibarra",
        descripcion="x" * 10,
        encuentro="x" * 10,
        latitud="0.35",
        longitud="-78.12",
        estado=Comunidad.Estado.PUBLICADA,
    )
    return responsable, voluntario, comunidad


def test_solicitar_aprobar_y_retirar_miembro(client, escenario):
    responsable, voluntario, comunidad = escenario
    client.force_login(voluntario)
    solicitar = reverse("comunidades:solicitar_membresia", args=[comunidad.pk])
    assert (
        client.post(
            solicitar,
            {
                "fecha_nacimiento": "1990-05-01",
                "genero": "femenino",
                "confirmar_solicitud": "on",
            },
        ).status_code
        == 302
    )
    miembro = Miembro.objects.get(usuario=voluntario)
    assert miembro.estado == Miembro.Estado.SOLICITADA
    assert miembro.comunidad_id == comunidad.pk
    assert miembro.nivel == Miembro.Nivel.APRENDIZ
    assert miembro.puntos == 0
    assert (
        client.post(
            solicitar,
            {
                "fecha_nacimiento": "1990-05-01",
                "genero": "femenino",
                "confirmar_solicitud": "on",
            },
        ).status_code
        == 302
    )
    miembro.refresh_from_db()
    assert miembro.estado == Miembro.Estado.SOLICITADA
    client.force_login(responsable)
    gestionar = reverse("comunidades:gestionar_miembros", args=[comunidad.pk])
    assert list(client.get(gestionar).context["solicitudes"]) == [miembro]
    decidir = reverse("comunidades:decidir_miembro", args=[comunidad.pk, miembro.pk])
    assert client.post(decidir, {"accion": "aprobar"}).status_code == 302
    miembro.refresh_from_db()
    assert miembro.estado == Miembro.Estado.APROBADA
    assert b"Aprendiz" in client.get(gestionar).content
    retirar = reverse("comunidades:retirar_miembro", args=[comunidad.pk, miembro.pk])
    assert client.post(retirar).status_code == 302
    miembro.refresh_from_db()
    assert miembro.estado == Miembro.Estado.RETIRADA


def test_no_puede_tener_dos_comunidades_a_la_vez(client, escenario, django_user_model):
    responsable, voluntario, comunidad = escenario
    otra = Comunidad.objects.create(
        responsable=responsable,
        nombre="Huerto Otavalo",
        provincia="Imbabura",
        localidad="Otavalo",
        descripcion="x" * 10,
        encuentro="x" * 10,
        latitud="0.23",
        longitud="-78.26",
        estado=Comunidad.Estado.PUBLICADA,
    )
    client.force_login(voluntario)
    client.post(
        reverse("comunidades:solicitar_membresia", args=[comunidad.pk]),
        {
            "fecha_nacimiento": "1990-05-01",
            "genero": "femenino",
            "confirmar_solicitud": "on",
        },
    )
    r = client.post(
        reverse("comunidades:solicitar_membresia", args=[otra.pk]),
        {
            "fecha_nacimiento": "1990-05-01",
            "genero": "femenino",
            "confirmar_solicitud": "on",
        },
    )
    assert r.status_code == 302
    assert Miembro.objects.get(usuario=voluntario).comunidad_id == comunidad.pk


def test_gestion_solo_del_responsable(client, escenario):
    _responsable, voluntario, comunidad = escenario
    client.force_login(voluntario)
    assert (
        client.get(
            reverse("comunidades:gestionar_miembros", args=[comunidad.pk]),
        ).status_code
        == 404
    )


def test_agregar_por_codigo(client, escenario):
    responsable, voluntario, comunidad = escenario
    voluntario.fecha_nacimiento = date(1992, 3, 15)
    voluntario.genero = "masculino"
    voluntario.save()
    client.force_login(responsable)
    agregar = reverse("comunidades:agregar_por_codigo", args=[comunidad.pk])
    assert client.post(agregar, {"codigo": voluntario.codigo_unico}).status_code == 302
    miembro = Miembro.objects.get(usuario=voluntario)
    assert miembro.estado == Miembro.Estado.APROBADA
    assert miembro.comunidad_id == comunidad.pk
    assert miembro.fecha_nacimiento == date(1992, 3, 15)
    assert miembro.genero == "masculino"


def test_agregar_por_codigo_exige_fecha_nacimiento(client, escenario):
    responsable, voluntario, comunidad = escenario
    voluntario.fecha_nacimiento = None
    voluntario.save()
    client.force_login(responsable)
    agregar = reverse("comunidades:agregar_por_codigo", args=[comunidad.pk])
    assert client.post(agregar, {"codigo": voluntario.codigo_unico}).status_code == 302
    assert not Miembro.objects.filter(usuario=voluntario).exists()


def test_agregar_por_codigo_codigo_inexistente(client, escenario):
    responsable, _voluntario, comunidad = escenario
    client.force_login(responsable)
    agregar = reverse("comunidades:agregar_por_codigo", args=[comunidad.pk])
    assert client.post(agregar, {"codigo": "000000"}).status_code == 302
    assert Miembro.objects.count() == 0


def test_agregar_por_codigo_solo_el_responsable(client, escenario):
    _responsable, voluntario, comunidad = escenario
    client.force_login(voluntario)
    agregar = reverse("comunidades:agregar_por_codigo", args=[comunidad.pk])
    assert client.post(agregar, {"codigo": voluntario.codigo_unico}).status_code == 404


def test_proponer_y_certificar_talento(client, escenario):
    responsable, voluntario, comunidad = escenario
    client.force_login(voluntario)
    client.post(
        reverse("comunidades:solicitar_membresia", args=[comunidad.pk]),
        {
            "fecha_nacimiento": "1990-05-01",
            "genero": "femenino",
            "confirmar_solicitud": "on",
        },
    )
    miembro = Miembro.objects.get(usuario=voluntario)
    client.force_login(responsable)
    client.post(
        reverse("comunidades:decidir_miembro", args=[comunidad.pk, miembro.pk]),
        {"accion": "aprobar"},
    )
    proponer = reverse("comunidades:proponer_talento", args=[comunidad.pk, miembro.pk])
    client.post(proponer, {"talento": "Injerto de romero"})
    client.post(proponer, {"talento": "Injerto de romero"})
    assert (
        CertificacionTalento.objects.filter(
            miembro=miembro,
            talento="Injerto de romero",
        ).count()
        == 1
    )
    cert = CertificacionTalento.objects.get(
        miembro=miembro,
        talento="Injerto de romero",
    )
    assert cert.estado == CertificacionTalento.Estado.PROPUESTA
    assert cert.propuesto_por == responsable
