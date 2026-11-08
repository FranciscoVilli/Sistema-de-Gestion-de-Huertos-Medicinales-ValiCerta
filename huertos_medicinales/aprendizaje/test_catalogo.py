import pytest
from django.urls import reverse

from huertos_medicinales.aprendizaje.catalogo import PLANTAS
from huertos_medicinales.aprendizaje.catalogo import UMBRAL_CICLO_CORTO_DIAS
from huertos_medicinales.aprendizaje.catalogo import ciclo

pytestmark = pytest.mark.django_db


def test_cada_planta_tiene_datos_basicos_y_fuentes_consistentes():
    for planta in PLANTAS:
        assert planta["familia_botanica"]
        assert planta["ciclo"] == ciclo(planta)
        assert (planta["ciclo"] == "corto") == (planta["dias_madurez"] <= UMBRAL_CICLO_CORTO_DIAS)
        # Si hay clasificación caliente/fría, debe traer su fuente; nunca una sin la otra.
        assert bool(planta["temperatura"]) == bool(planta["fuente_temperatura_nombre"])
        assert bool(planta["temperatura"]) == bool(planta["fuente_temperatura_url"])
        assert bool(planta["provincias"]) == bool(planta["fuente_distribucion_nombre"])
        assert bool(planta["provincias"]) == bool(planta["fuente_distribucion_url"])


def test_manzanilla_menta_romero_documentadas_como_calientes_segun_msp():
    por_slug = {planta["slug"]: planta for planta in PLANTAS}
    for slug in ("manzanilla", "menta", "romero"):
        assert por_slug[slug]["temperatura"] == "caliente"
    # La caléndula no aparece en la fuente consultada (MSP, 2017): no se asume.
    assert por_slug["calendula"]["temperatura"] == ""


def test_ficha_de_planta_muestra_clasificacion_cuando_esta_documentada(client, django_user_model):
    user = django_user_model.objects.create_user(email="catalogo-student@example.invalid")
    client.force_login(user)
    response = client.get(reverse("learning_plant", args=["romero"]))
    assert response.status_code == 200
    assert b"Planta caliente" in response.content
    assert b"Lamiaceae" in response.content
