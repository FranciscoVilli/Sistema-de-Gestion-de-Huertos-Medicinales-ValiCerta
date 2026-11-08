from pathlib import Path

import pytest
from django.core.management import call_command
from django.urls import reverse

from huertos_medicinales.aprendizaje.educational_models import CapituloEducativo
from huertos_medicinales.aprendizaje.educational_models import CompetenciaAdquirida
from huertos_medicinales.aprendizaje.educational_models import EvaluacionEducativa
from huertos_medicinales.aprendizaje.educational_models import IntentoCapitulo
from huertos_medicinales.aprendizaje.educational_models import LeccionEducativa
from huertos_medicinales.aprendizaje.educational_models import ProgresoLeccion
from huertos_medicinales.aprendizaje.test_pilot import finish_reading
from huertos_medicinales.aprendizaje.test_pilot import start
from huertos_medicinales.aprendizaje.test_pilot import submit

pytestmark = pytest.mark.django_db


@pytest.fixture
def curriculum(client, django_user_model):
    call_command("seed_curriculum", verbosity=0)
    user = django_user_model.objects.create_user(email="curriculum-student@example.invalid")
    client.force_login(user)
    return user


def test_all_chapters_have_valid_content_assets_and_assessments(curriculum):
    assert CapituloEducativo.objects.filter(estado="publicado").count() == 24
    assert LeccionEducativa.objects.count() == 27
    assert EvaluacionEducativa.objects.count() == 24
    static = Path(__file__).resolve().parents[1] / "static"
    for lesson in LeccionEducativa.objects.filter(slug__startswith="capitulo-"):
        lesson.full_clean()
        assert len(lesson.secciones) == 4
        assert all(len(section["texto"].split()) >= 20 for section in lesson.secciones)
        assert lesson.fuentes.count() >= 1
        assert (static / lesson.secciones[0]["imagen"]).is_file()
        assert len(lesson.secciones[1]["explorar"]) == 3
        assert len(lesson.secciones[2]["caso"]["opciones"]) == 3
        assert lesson.secciones[3]["practica"]
        exam = lesson.capitulo.evaluacion
        exam.full_clean()
        assert exam.competencias.exists()
        assert len(exam.preguntas) >= 3


def test_seed_is_idempotent_and_preserves_editor_changes_and_progress(curriculum):
    lesson = LeccionEducativa.objects.get(slug="capitulo-1-contenido")
    lesson.titulo = "Edición propia del administrador"
    lesson.save()
    progress = ProgresoLeccion.objects.create(user=curriculum, leccion=lesson, revision=lesson.revision, seccion=2)
    count = lesson.historial.count()
    call_command("seed_curriculum", verbosity=0)
    lesson.refresh_from_db(); progress.refresh_from_db()
    assert lesson.titulo == "Edición propia del administrador"
    assert lesson.historial.count() == count
    assert progress.seccion == 2
    assert LeccionEducativa.objects.count() == 27
    assert len(EvaluacionEducativa.objects.get(capitulo__numero=5).preguntas) == 6


def test_every_chapter_reader_and_assessment_end_to_end(client, curriculum):
    for chapter in CapituloEducativo.objects.all():
        assert client.get(reverse("lms_block", args=[chapter.bloque_id])).status_code == 200
        assert client.get(reverse("lms_chapter", args=[chapter.slug])).status_code == 200
        lesson = chapter.lecciones.get(slug=f"capitulo-{chapter.numero}-contenido")
        response = client.get(reverse("lms_lesson", args=[lesson.slug]))
        assert response.status_code == 200
        assert "edu-visual" in response.content.decode()
        finish_reading(client, chapter)
        for section, expected in [(1, "Explora las ideas"), (2, "PRÁCTICA SIN NOTA"), (3, "Tu pequeña investigación")]:
            response = client.get(reverse("lms_lesson", args=[lesson.slug]), {"seccion": section})
            assert response.status_code == 200
            assert expected in response.content.decode()
        attempt = start(client, chapter)
        response = submit(client, attempt)
        assert response.status_code == 302
        attempt.refresh_from_db()
        assert attempt.aprobado and attempt.porcentaje == 100
        assert client.get(reverse("lms_result", args=[attempt.pk])).status_code == 200
    assert IntentoCapitulo.objects.filter(user=curriculum, aprobado=True).count() == 24
    assert CompetenciaAdquirida.objects.filter(user=curriculum).count() == 25
    dashboard = client.get(reverse("learning"))
    assert dashboard.context["progress"] == 100
    assert dashboard.context["total_count"] == 27
    assert "Los demás capítulos están en preparación" not in dashboard.content.decode()

