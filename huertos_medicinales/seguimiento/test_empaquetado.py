from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone

from .models import Empaquetado
from .models import Practica

pytestmark = pytest.mark.django_db


@pytest.fixture
def practica(django_user_model):
    user = django_user_model.objects.create_user(email="empaquetado@example.com")
    otro = django_user_model.objects.create_user(email="otro-empaquetado@example.com")
    cultivo = Practica.objects.create(
        participante=user,
        titulo="Romero en maceta",
        planta="romero",
        inicio=timezone.localdate(),
        espacio="Patio",
        objetivo="Observar cambios",
    )
    return user, otro, cultivo


def test_registrar_empaquetado_muestra_caducidad_y_queda_en_bitacora(client, practica):
    user, otro, cultivo = practica
    client.force_login(user)
    url = reverse("seguimiento:empaquetar", args=[cultivo.pk])
    assert client.get(url).status_code == 200
    response = client.post(url, {
        "peso_gramos": "100",
        "indicaciones": "Infusión después de comidas",
        "dosificacion": "Una cucharadita por taza",
        "contraindicaciones": "No usar en embarazo sin supervisión",
        "region": "sierra",
        "fecha_empaquetado": date(2026, 1, 1).isoformat(),
    })
    assert response.status_code == 302
    empaquetado = Empaquetado.objects.get(practica=cultivo)
    assert empaquetado.fecha_caducidad == date(2027, 1, 1)
    detalle = client.get(reverse("seguimiento:detalle", args=[cultivo.pk]))
    assert b"Registrar empaquetado" in detalle.content


def test_empaquetado_requiere_ser_el_propietario(client, practica):
    user, otro, cultivo = practica
    client.force_login(otro)
    assert client.get(reverse("seguimiento:empaquetar", args=[cultivo.pk])).status_code == 404


def test_video_url_se_muestra_en_la_bitacora(client, practica):
    user, otro, cultivo = practica
    client.force_login(user)
    url = reverse("seguimiento:detalle", args=[cultivo.pk])
    response = client.post(url, {
        "fecha": timezone.localdate().isoformat(),
        "accion": "Riego",
        "resultado": "Sigue verde",
        "pregunta": "",
        "video_url": "https://example.com/mi-video",
    })
    assert response.status_code == 302
    bitacora = client.get(url)
    assert b"example.com/mi-video" in bitacora.content
