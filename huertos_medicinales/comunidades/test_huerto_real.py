import pytest
from django.urls import reverse

from .models import Bodega
from .models import Comunidad
from .models import HuertoReal

pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario(client, django_user_model):
    responsable = django_user_model.objects.create_user(
        email="responsable-huerto@example.com",
    )
    otro = django_user_model.objects.create_user(email="otro-huerto@example.com")
    comunidad = Comunidad.objects.create(
        responsable=responsable,
        nombre="Huerto Real Ibarra",
        provincia="Imbabura",
        localidad="Ibarra",
        descripcion="x" * 10,
        encuentro="x" * 10,
        latitud="0.35",
        longitud="-78.12",
        estado=Comunidad.Estado.PUBLICADA,
    )
    client.force_login(responsable)
    return responsable, otro, comunidad


def payload(**overrides):
    data = {
        "provincia": "Imbabura",
        "parroquia": "San Antonio",
        "plantas": ["romero"],
        "tipo_diseno": "en_tierra",
        "tecnica_diseno": "Surcos",
        "tipo_cerca": "viva",
        "detalle_cerca": "Higuerilla y floripondio",
        "area_total": "45.5",
        "unidad_area": "m2",
        "detalle_riego": "Canal comunitario los martes",
        "detalle_abono": "Compost propio",
        "tiene_espacio_herramientas": "on",
        "detalle_herramientas": "Estante de madera",
        "tiene_espacio_semillas": "on",
        "detalle_semillas": "",
        "tiene_espacio_abonos": "",
        "detalle_abonos": "",
    }
    data.update(overrides)
    return data


def test_responsable_registra_huerto_real_y_bodega(client, escenario):
    _responsable, _otro, comunidad = escenario
    url = reverse("comunidades:huerto_real", args=[comunidad.pk])
    assert client.get(url).status_code == 200
    assert client.post(url, payload()).status_code == 302
    huerto = HuertoReal.objects.get(comunidad=comunidad)
    assert huerto.tipo_diseno == "en_tierra"
    assert huerto.tipo_cerca == "viva"
    assert str(huerto.area_total) == "45.50"
    assert huerto.plantas == ["romero"]
    assert huerto.plantas_nombres == ["Romero"]
    bodega = Bodega.objects.get(huerto_real=huerto)
    assert bodega.tiene_espacio_herramientas
    assert bodega.tiene_espacio_semillas
    assert not bodega.tiene_espacio_abonos
    detalle = client.get(reverse("comunidades:detalle", args=[comunidad.pk]))
    assert b"Higuerilla y floripondio" in detalle.content


def test_suelo_agua_abono_se_recomiendan_segun_la_planta_elegida(client, escenario):
    _responsable, _otro, comunidad = escenario
    url = reverse("comunidades:huerto_real", args=[comunidad.pk])
    assert client.post(url, payload(plantas=["romero"])).status_code == 302
    huerto = HuertoReal.objects.get(comunidad=comunidad)
    assert huerto.tipo_suelo == "arenoso"
    assert huerto.tipo_agua_riego == "goteo"
    assert huerto.tipo_abono == ""


def test_sin_recomendacion_confirmada_el_campo_queda_vacio(client, escenario):
    _responsable, _otro, comunidad = escenario
    url = reverse("comunidades:huerto_real", args=[comunidad.pk])
    assert client.post(url, payload(plantas=["menta"])).status_code == 302
    huerto = HuertoReal.objects.get(comunidad=comunidad)
    assert huerto.tipo_suelo == ""
    assert huerto.tipo_agua_riego == ""
    assert huerto.tipo_abono == ""


def test_editar_reutiliza_el_mismo_registro(client, escenario):
    _responsable, _otro, comunidad = escenario
    url = reverse("comunidades:huerto_real", args=[comunidad.pk])
    client.post(url, payload())
    nueva = payload()
    nueva["area_total"] = "60.0"
    client.post(url, nueva)
    assert HuertoReal.objects.filter(comunidad=comunidad).count() == 1
    assert str(HuertoReal.objects.get(comunidad=comunidad).area_total) == "60.00"


def test_solo_el_responsable_puede_gestionar_el_huerto_real(client, escenario):
    _responsable, otro, comunidad = escenario
    client.force_login(otro)
    url = reverse("comunidades:huerto_real", args=[comunidad.pk])
    assert client.get(url).status_code == 404
    assert client.post(url, payload()).status_code == 404
