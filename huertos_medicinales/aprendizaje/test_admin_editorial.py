"""La gestion editorial del contenido educativo (HU-015) debe estar en /admin/."""

from http import HTTPStatus

import pytest
from django.contrib import admin
from django.urls import reverse

from .educational_models import CapituloEducativo
from .educational_models import EvaluacionEducativa
from .educational_models import LeccionEducativa
from .educational_models import RutaEducativa

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "modelo",
    [LeccionEducativa, CapituloEducativo, EvaluacionEducativa, RutaEducativa],
)
def test_contenido_educativo_registrado_en_el_admin(modelo):
    assert admin.site.is_registered(modelo)


def test_administrador_abre_la_lista_de_lecciones(admin_client):
    url = reverse("admin:aprendizaje_leccioneducativa_changelist")
    assert admin_client.get(url).status_code == HTTPStatus.OK
