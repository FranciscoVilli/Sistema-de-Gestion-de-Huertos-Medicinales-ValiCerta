from datetime import timedelta
from http import HTTPStatus
from io import BytesIO

import pytest
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from huertos_medicinales.aprendizaje.catalogo import LECCIONES
from huertos_medicinales.aprendizaje.catalogo import XP_POR_LECCION
from huertos_medicinales.aprendizaje.models import Logro

from .models import Devolucion
from .models import EventoPractica
from .models import Practica

pytestmark = pytest.mark.django_db


@pytest.fixture
def usuario(django_user_model):
    user = django_user_model.objects.create_user(email="cultivo@example.com")
    Logro.objects.create(user=user, leccion=LECCIONES[0]["slug"], xp=XP_POR_LECCION)
    return user


@pytest.fixture
def practica(usuario):
    return Practica.objects.create(
        participante=usuario,
        titulo="Mi cultivo",
        planta="manzanilla",
        inicio=timezone.localdate(),
        espacio="Maceta",
        objetivo="Observar cambios",
    )


def datos():
    return {
        "titulo": "Mi cultivo",
        "planta": "manzanilla",
        "inicio": timezone.localdate().isoformat(),
        "espacio": "Maceta",
        "objetivo": "Observar cambios",
    }


def test_practica_se_guarda_con_propietario_y_evento(
    client,
    usuario,
    django_user_model,
):
    otro = django_user_model.objects.create_user(email="otro@example.com")
    client.force_login(usuario)
    response = client.post(
        reverse("seguimiento:crear"),
        {**datos(), "participante": otro.pk, "estado": "finalizada"},
    )
    assert response.status_code == HTTPStatus.FOUND
    practica = Practica.objects.get()
    assert practica.participante == usuario
    assert practica.estado == "activa"
    assert practica.planta_nombre == "Manzanilla"
    assert EventoPractica.objects.get().accion == "creada"
    assert Logro.objects.count() == 1


def test_sin_leccion_se_puede_registrar_cultivo_real(client, django_user_model):
    nuevo = django_user_model.objects.create_user(email="recien-llegado@example.com")
    client.force_login(nuevo)
    assert client.get(reverse("seguimiento:crear")).status_code == HTTPStatus.OK
    assert client.post(reverse("seguimiento:crear"), datos()).status_code == HTTPStatus.FOUND
    assert Practica.objects.get().participante == nuevo
    assert not Logro.objects.exists()


def test_se_puede_elegir_especie_sin_desbloqueo_educativo(client, usuario):
    client.force_login(usuario)
    response = client.post(reverse("seguimiento:crear"), {**datos(), "planta": "menta"})
    assert response.status_code == HTTPStatus.FOUND
    assert Practica.objects.get().planta == "menta"


def test_otro_usuario_no_puede_leer_editar_ni_cerrar(
    client,
    practica,
    django_user_model,
):
    client.force_login(django_user_model.objects.create_user(email="ajeno@example.com"))
    for name in ["detalle", "editar", "estado"]:
        url = reverse(f"seguimiento:{name}", args=[practica.pk])
        assert (
            client.post(url, {"estado": "finalizada", **datos()}).status_code
            == HTTPStatus.NOT_FOUND
        )
    practica.refresh_from_db()
    assert practica.estado == "activa"


def test_fechas_futuras_no_crean_practicas(client, usuario):
    client.force_login(usuario)
    response = client.post(
        reverse("seguimiento:crear"),
        {**datos(), "inicio": timezone.localdate() + timedelta(days=1)},
    )
    assert response.status_code == HTTPStatus.OK
    assert not Practica.objects.exists()


def test_observaciones_persisten_con_foto_y_no_admiten_fechas_anteriores(
    client,
    usuario,
    practica,
):
    client.force_login(usuario)
    url = reverse("seguimiento:detalle", args=[practica.pk])

    def nueva_foto():
        buffer = BytesIO()
        Image.new("RGB", (2, 2), color="green").save(buffer, format="JPEG")
        return SimpleUploadedFile(
            "siembra.jpg",
            buffer.getvalue(),
            content_type="image/jpeg",
        )

    def datos_observacion(**overrides):
        return {
            "fecha": timezone.localdate(),
            "accion": "Revisé el suelo",
            "resultado": "Húmedo",
            "pregunta": "",
            "foto": nueva_foto(),
            **overrides,
        }

    assert (
        client.post(
            url,
            datos_observacion(fecha=timezone.localdate() - timedelta(days=1)),
        ).status_code
        == HTTPStatus.OK
    )
    assert practica.observaciones.count() == 0
    assert client.post(url, datos_observacion()).status_code == HTTPStatus.FOUND
    assert practica.observaciones.count() == 1
    assert practica.observaciones.get().foto
    assert practica.eventos.get().detalle["resultado"] == "Húmedo"
    assert "Húmedo" in client.get(url).content.decode()


def test_etapa_se_calcula_con_dias_reales_y_adelanto(usuario):
    dias_sembrados = 5
    dias_de_adelanto = 60
    practica = Practica.objects.create(
        participante=usuario,
        titulo="Mi cultivo",
        planta="manzanilla",
        inicio=timezone.localdate() - timedelta(days=dias_sembrados),
        espacio="Maceta",
        objetivo="Observar cambios",
    )
    assert practica.dias_transcurridos == dias_sembrados
    assert practica.etapa == "semilla"
    practica.dias_adelanto = dias_de_adelanto
    practica.save(update_fields=["dias_adelanto"])
    assert practica.etapa == "madura"


def test_cerrar_reabrir_y_editar_conserva_historial(client, usuario, practica):
    client.force_login(usuario)
    state_url = reverse("seguimiento:estado", args=[practica.pk])
    assert client.get(state_url).status_code == HTTPStatus.METHOD_NOT_ALLOWED
    client.post(state_url, {"estado": "finalizada"})
    client.post(
        reverse("seguimiento:detalle", args=[practica.pk]),
        {"fecha": timezone.localdate(), "accion": "Agua", "resultado": "Cambio"},
    )
    assert practica.observaciones.count() == 0
    client.post(state_url, {"estado": "activa"})
    client.post(
        reverse("seguimiento:editar", args=[practica.pk]),
        {**datos(), "titulo": "Título corregido"},
    )
    practica.refresh_from_db()
    assert practica.titulo == "Título corregido"
    assert list(practica.eventos.values_list("accion", flat=True)) == [
        "actualizada",
        "estado",
        "estado",
    ]


def test_solo_facilitador_autorizado_registra_orientacion(
    client,
    usuario,
    practica,
    django_user_model,
):
    url = reverse("seguimiento:revisar", args=[practica.pk])
    client.force_login(usuario)
    assert (
        client.post(url, {"texto": "No autorizada"}).status_code == HTTPStatus.FORBIDDEN
    )
    facilitador = django_user_model.objects.create_user(email="facilitador@example.com")
    facilitador.user_permissions.add(
        Permission.objects.get(codename="revisar_practica"),
    )
    client.force_login(facilitador)
    assert (
        client.post(url, {"texto": "Compara una condición a la vez"}).status_code
        == HTTPStatus.FOUND
    )
    assert Devolucion.objects.get().facilitador == facilitador
    client.force_login(usuario)
    assert (
        "Compara una condición"
        in client.get(
            reverse("seguimiento:detalle", args=[practica.pk]),
        ).content.decode()
    )


def test_admin_adelanta_tiempo_con_permiso_y_registra_evento(
    client,
    practica,
    django_user_model,
):
    admin = django_user_model.objects.create_user(
        email="admin@example.com",
        is_staff=True,
    )
    admin.user_permissions.add(
        Permission.objects.get(codename="avanzar_tiempo_practica"),
        Permission.objects.get(codename="view_practica"),
    )
    client.force_login(admin)
    response = client.post(
        reverse("admin:seguimiento_practica_changelist"),
        {
            "action": "adelantar_una_semana",
            "_selected_action": [str(practica.pk)],
        },
    )
    assert response.status_code == HTTPStatus.FOUND
    practica.refresh_from_db()
    dias_por_adelanto = 7
    assert practica.dias_adelanto == dias_por_adelanto
    assert practica.eventos.filter(accion="adelanto_tiempo").exists()


def test_csrf_y_autenticacion_protegen_escrituras(client, usuario):

    assert client.get(reverse("seguimiento:listado")).status_code == HTTPStatus.FOUND
    protected = Client(enforce_csrf_checks=True)
    protected.force_login(usuario)
    assert (
        protected.post(reverse("seguimiento:crear"), datos()).status_code
        == HTTPStatus.FORBIDDEN
    )
