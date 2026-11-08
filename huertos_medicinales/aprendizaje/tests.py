from http import HTTPStatus
from secrets import token_urlsafe

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from .catalogo import LECCIONES
from .models import IntentoEvaluacion
from .models import Logro
from .services import completar
from .services import estado

pytestmark = pytest.mark.django_db
EXPECTED_LESSON_XP = 25
EXPECTED_ATTEMPTS = 2
VERSION_HASH_LENGTH = 64


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(
        email="student@example.com",
        password=token_urlsafe(24),
    )


def finish(user, count):
    for item in LECCIONES[:count]:
        assert completar(user, item["slug"], item["correcta"]) == "completada"


def test_new_account_starts_at_zero(student):
    result = estado(student)
    assert result["xp"] == 0
    assert result["nivel"] == "Aprendiz"
    assert result["plantas_abiertas"] == 0
    assert result["lecciones"][0]["abierta"]
    assert not result["lecciones"][1]["abierta"]


def test_wrong_answer_does_not_award_xp(student):
    assert completar(student, LECCIONES[0]["slug"], "wrong") == "incorrecta"
    assert estado(student)["xp"] == 0


def test_cannot_skip_locked_lesson(student):
    assert (
        completar(student, LECCIONES[1]["slug"], LECCIONES[1]["correcta"])
        == "bloqueada"
    )
    assert not Logro.objects.filter(user=student).exists()


def test_same_lesson_cannot_award_twice(student):
    finish(student, 1)
    assert (
        completar(student, LECCIONES[0]["slug"], LECCIONES[0]["correcta"]) == "repetida"
    )
    assert estado(student)["xp"] == EXPECTED_LESSON_XP
    assert Logro.objects.filter(user=student).count() == 1


@pytest.mark.parametrize(
    ("count", "xp", "level", "plants"),
    [
        (2, 50, "Aprendiz", 2),
        (3, 75, "Oficial", 2),
        (4, 100, "Oficial", 3),
        (6, 150, "Maestro", 4),
    ],
)
def test_thresholds_and_unlocks(student, count, xp, level, plants):
    finish(student, count)
    result = estado(student)
    assert (result["xp"], result["nivel"], result["plantas_abiertas"]) == (
        xp,
        level,
        plants,
    )


def test_progress_is_private_to_account(student, django_user_model):
    other = django_user_model.objects.create_user(email="other@example.com")
    finish(student, 2)
    assert estado(other)["xp"] == 0
    assert estado(AnonymousUser())["xp"] == 0


def test_botanical_info_is_available_without_progress(client, student):
    client.force_login(student)
    response = client.get(reverse("learning_plant", args=["menta"]))
    assert response.status_code == HTTPStatus.OK
    finish(student, 2)
    assert (
        client.get(reverse("learning_plant", args=["menta"])).status_code
        == HTTPStatus.OK
    )


def test_post_ignores_forged_points(client, student):
    client.force_login(student)
    response = client.post(
        reverse("learning_lesson", args=[LECCIONES[0]["slug"]]),
        {"answer": LECCIONES[0]["correcta"], "xp": "99999"},
    )
    assert response.status_code == HTTPStatus.FOUND
    assert estado(student)["xp"] == EXPECTED_LESSON_XP


def test_lesson_get_does_not_award_xp(client, student):
    client.force_login(student)
    assert (
        client.get(reverse("learning_lesson", args=[LECCIONES[0]["slug"]])).status_code
        == HTTPStatus.OK
    )
    assert estado(student)["xp"] == 0


def test_intentos_conservan_resultado_y_contenido_sin_duplicar_xp(student):

    lesson = LECCIONES[0]
    assert completar(student, lesson["slug"], "2") == "incorrecta"
    assert completar(student, lesson["slug"], lesson["correcta"]) == "completada"
    assert IntentoEvaluacion.objects.filter(user=student).count() == EXPECTED_ATTEMPTS
    saved = IntentoEvaluacion.objects.filter(user=student).first()
    assert saved.resultado == "completada"
    assert saved.contenido["pregunta"] == lesson["pregunta"]
    assert len(saved.version_contenido) == VERSION_HASH_LENGTH
    assert estado(student)["xp"] == EXPECTED_LESSON_XP


def test_learning_dashboard_sections_and_search(client, student):
    client.force_login(student)
    for section in ["ruta", "lecciones", "plantas", "guias", "avances"]:
        response = client.get(reverse("learning"), {"seccion": section})
        assert response.status_code == 200
        assert response.context["section"] == section
    response = client.get(reverse("learning"), {"q": "calendula"})
    assert [p["slug"] for p in response.context["results_plants"]] == ["calendula"]
    assert client.get(reverse("learning_plant", args=["calendula"])).status_code == 200
    response = client.get(reverse("learning"), {"q": "zzzznotfound"})
    assert not response.context["results_plants"] and not response.context["results_lessons"]
    finish(student, 2)
    response = client.get(reverse("learning"))
    assert response.context["progress"] == 0
    assert response.context["next_lesson"] is None
    assert Logro.objects.filter(user=student).count() == 2
    assert client.get(reverse("learning_lesson",args=[LECCIONES[3]["slug"]])).status_code == 302
    client.logout()
    assert client.get(reverse("learning_preview")).status_code == 200
