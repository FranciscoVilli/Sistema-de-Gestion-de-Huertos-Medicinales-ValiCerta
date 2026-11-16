import pytest
from django.core.management import call_command
from django.urls import reverse

from huertos_medicinales.aprendizaje.educational_models import CapituloEducativo
from huertos_medicinales.aprendizaje.educational_models import RutaEducativa
from huertos_medicinales.aprendizaje.educational_services import chapter_unlocked
from huertos_medicinales.aprendizaje.educational_services import lesson_unlocked
from huertos_medicinales.aprendizaje.test_pilot import complete_lesson
from huertos_medicinales.aprendizaje.test_pilot import start
from huertos_medicinales.aprendizaje.test_pilot import submit

pytestmark = pytest.mark.django_db


@pytest.fixture
def curriculum(client, django_user_model):
    call_command("seed_curriculum", verbosity=0)
    user = django_user_model.objects.create_user(
        email="sequential-student@example.invalid",
    )
    client.force_login(user)
    return user


def test_second_chapter_locked_until_first_is_approved(client, curriculum):
    first = CapituloEducativo.objects.get(numero=1)
    second = CapituloEducativo.objects.get(numero=2)
    assert chapter_unlocked(curriculum, first)
    assert not chapter_unlocked(curriculum, second)
    response = client.get(reverse("lms_chapter", args=[second.slug]))
    assert response.status_code == 302
    assert response.url == reverse("lms_catalog")
    lesson = first.lecciones.get(slug="capitulo-1-contenido")
    complete_lesson(client, lesson)
    attempt = start(client, first)
    submit(client, attempt)
    assert chapter_unlocked(curriculum, second)
    response = client.get(reverse("lms_chapter", args=[second.slug]))
    assert response.status_code == 302
    assert response.url == reverse(
        "lms_lesson",
        args=[second.lecciones.order_by("orden").first().slug],
    )


def test_lesson_order_is_enforced_within_a_chapter(client, curriculum):
    for numero in (1, 2, 3, 4):
        earlier = CapituloEducativo.objects.get(numero=numero)
        complete_lesson(
            client,
            earlier.lecciones.get(slug=f"capitulo-{numero}-contenido"),
        )
        submit(client, start(client, earlier))
    chapter = CapituloEducativo.objects.get(numero=5)
    assert chapter_unlocked(curriculum, chapter)
    lessons = list(chapter.lecciones.order_by("orden"))
    assert len(lessons) == 4
    first, second = lessons[0], lessons[1]
    assert lesson_unlocked(curriculum, first)
    assert not lesson_unlocked(curriculum, second)
    response = client.get(reverse("lms_lesson", args=[second.slug]))
    assert response.status_code == 302
    assert response.url == reverse(
        "lms_chapter",
        args=[chapter.slug],
    )
    complete_lesson(client, first)
    assert lesson_unlocked(curriculum, second)
    assert client.get(reverse("lms_lesson", args=[second.slug])).status_code == 200


def test_seed_plant_routes_maps_every_catalog_species(curriculum):
    call_command("seed_plant_routes", verbosity=0)
    mapped = set(
        RutaEducativa.objects.filter(
            slug__in=[
                "manzanilla-fundamentos",
                "menta-siembra-propagacion",
                "calendula-sanidad-vegetal",
                "romero-cosecha",
            ],
        ).values_list("especie", flat=True),
    )
    assert mapped == {"manzanilla", "menta", "calendula", "romero"}
    call_command("seed_plant_routes", verbosity=0)
    assert RutaEducativa.objects.filter(especie="menta").count() == 1
