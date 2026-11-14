from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

if TYPE_CHECKING:
    from huertos_medicinales.users.models import User

pytestmark = pytest.mark.django_db


def _imagen():
    buffer = BytesIO()
    Image.new("RGB", (2, 2), color="green").save(buffer, format="PNG")
    return SimpleUploadedFile("foto.png", buffer.getvalue(), content_type="image/png")


def test_foto_se_actualiza_al_subir_una_imagen_valida(client, user: User):
    client.force_login(user)
    response = client.post(reverse("users:foto"), {"foto": _imagen()})
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.foto


def test_foto_requiere_autenticacion(client):
    response = client.post(reverse("users:foto"), {"foto": _imagen()})
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_foto_invalida_no_rompe_y_redirige(client, user: User):
    client.force_login(user)
    archivo = SimpleUploadedFile("no_es_imagen.txt", b"esto no es una imagen", content_type="text/plain")
    response = client.post(reverse("users:foto"), {"foto": archivo})
    assert response.status_code == 302
    user.refresh_from_db()
    assert not user.foto
