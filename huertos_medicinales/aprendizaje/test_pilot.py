import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from huertos_medicinales.aprendizaje.educational_admin import LessonAdminForm
from huertos_medicinales.aprendizaje.educational_models import *
from huertos_medicinales.aprendizaje.educational_services import route_status
from huertos_medicinales.seguimiento.models import Practica

pytestmark = pytest.mark.django_db


@pytest.fixture
def pilot(client, django_user_model):
    call_command("seed_education_pilot", verbosity=0)
    user = django_user_model.objects.create_user(email="pilot-student@example.com")
    other = django_user_model.objects.create_user(email="pilot-other@example.com")
    client.force_login(user)
    chapter = CapituloEducativo.objects.get(numero=5)
    return user, other, chapter


def finish_reading(client, chapter):
    for lesson in chapter.lecciones.all():
        url = reverse("lms_lesson", args=[lesson.slug])
        for i in range(len(lesson.secciones)):
            assert (
                client.post(
                    url, {"action": "next", "section": i, "revision": lesson.revision},
                ).status_code
                == 302
            )
        answer = [str(i) for i in lesson.comprension["correctas"]]
        assert (
            client.post(
                url, {"action": "answer", "revision": lesson.revision, "answer": answer},
            ).status_code
            == 302
        )


def start(client, chapter):
    response = client.post(
        reverse("lms_assessment", args=[chapter.slug]), {"action": "start"},
    )
    assert response.status_code == 302
    return IntentoCapitulo.objects.latest("pk")


def submit(client, attempt, wrong=False):
    payload = {
        "attempt": attempt.pk,
        "aprobado": "true",
        "porcentaje": "100",
        "user": "999",
    }
    for i, q in enumerate(attempt.contenido["preguntas"]):
        payload[f"q_{i}"] = ["999"] if wrong else [str(x) for x in q["correctas"]]
    return client.post(
        reverse("lms_assessment", args=[attempt.evaluacion.capitulo.slug]), payload,
    )


def test_structure_idempotence_and_draft_visibility(client, pilot):
    user, other, chapter = pilot
    assert (
        BloqueEducativo.objects.count() == 6 and CapituloEducativo.objects.count() == 24
    )
    assert LeccionEducativa.objects.count() == 3
    lesson = chapter.lecciones.first()
    lesson.titulo = "Edición conservada"
    lesson.save()
    call_command("seed_education_pilot", verbosity=0)
    lesson.refresh_from_db()
    assert lesson.titulo == "Edición conservada"
    assert LeccionEducativa.objects.count() == 3
    draft = CapituloEducativo.objects.get(numero=1)
    assert client.get(reverse("lms_chapter", args=[draft.slug])).status_code == 404
    assert client.get(reverse("lms_catalog")).status_code == 200
    assert client.get(reverse("lms_chapter", args=[chapter.slug])).status_code == 200


def test_progress_requires_server_steps_and_comprehension(client, pilot):
    user, other, chapter = pilot
    lesson = chapter.lecciones.first()
    url = reverse("lms_lesson", args=[lesson.slug])
    assert client.get(url).status_code == 200
    assert not ProgresoLeccion.objects.exists()
    client.post(url, {"action": "answer", "revision": lesson.revision, "answer": ["0"]})
    progress = ProgresoLeccion.objects.get()
    assert not progress.completada
    client.post(url, {"action": "next", "section": 99, "revision": lesson.revision})
    progress.refresh_from_db()
    assert progress.seccion == 0
    client.post(url, {"action": "next", "section": 0, "revision": lesson.revision})
    progress.refresh_from_db()
    assert progress.seccion == 1
    assert client.get(url).context["position"] == 1
    client.post(url, {"action": "next", "section": 0, "revision": lesson.revision})
    progress.refresh_from_db()
    assert progress.seccion == 1
    assert not ProgresoLeccion.objects.filter(user=other).exists()


def test_end_to_end_retry_competence_and_route(client, pilot):
    user, other, chapter = pilot
    route = RutaEducativa.objects.get()
    route_url = reverse("lms_route", args=[route.slug])
    assert client.post(route_url).status_code == 403
    assert (
        client.post(
            reverse("lms_assessment", args=[chapter.slug]), {"action": "start"},
        ).status_code
        == 200
    )
    assert not IntentoCapitulo.objects.exists()
    finish_reading(client, chapter)
    attempt = start(client, chapter)
    response = client.get(
        reverse("lms_assessment", args=[chapter.slug]), {"intento": attempt.pk},
    )
    assert response.status_code == 200 and b"correctas" not in response.content
    assert submit(client, attempt, wrong=True).status_code == 302
    attempt.refresh_from_db()
    assert attempt.porcentaje == 0 and not attempt.aprobado
    assert not CompetenciaAdquirida.objects.exists()
    retry = start(client, chapter)
    assert submit(client, retry).status_code == 302
    retry.refresh_from_db()
    assert retry.porcentaje == 100 and retry.aprobado
    assert CompetenciaAdquirida.objects.filter(user=user, intento=retry).count() == 1
    assert DesbloqueoRuta.objects.filter(user=user, ruta=route).count() == 1
    assert route_status(user, route)["eligible"]
    assert not route_status(other, route)["eligible"]
    assert submit(client, retry, wrong=True).status_code == 302
    retry.refresh_from_db()
    assert retry.porcentaje == 100
    assert client.get(reverse("lms_result", args=[retry.pk])).status_code == 200
    assert client.get(reverse("lms_progress")).status_code == 200
    assert client.post(route_url).status_code == 302
    assert DesbloqueoRuta.objects.get(user=user).iniciada
    assert not Practica.objects.exists()


def test_attempt_privacy_and_immutable_results(client, pilot):
    user, other, chapter = pilot
    finish_reading(client, chapter)
    attempt = start(client, chapter)
    submit(client, attempt)
    client.force_login(other)
    assert client.get(reverse("lms_result", args=[attempt.pk])).status_code == 404
    assert (
        client.get(
            reverse("lms_assessment", args=[chapter.slug]), {"intento": attempt.pk},
        ).status_code
        == 404
    )
    assert submit(client, attempt).status_code == 404
    assert (
        client.get(reverse("admin:aprendizaje_leccioneducativa_changelist")).status_code
        == 302
    )


def test_content_changes_invalidate_unfinished_attempt_and_keep_history(client, pilot):
    user, other, chapter = pilot
    finish_reading(client, chapter)
    attempt = start(client, chapter)
    lesson = chapter.lecciones.first()
    old = lesson.revision
    lesson.resumen = "Resumen revisado"
    lesson.save()
    assert lesson.revision == old + 1 and lesson.historial.count() >= 2
    assert submit(client, attempt).status_code == 200
    attempt.refresh_from_db()
    assert attempt.finalizado is None
    assert ProgresoLeccion.objects.filter(
        user=user, leccion=lesson, revision=old, completada=True,
    ).exists()
    assert (
        client.get(reverse("lms_lesson", args=[lesson.slug])).context["position"] == 0
    )


def test_editorial_validation_and_configurable_requirements(client, pilot):
    user, other, chapter = pilot
    lesson = chapter.lecciones.first()
    lesson.comprension = {}
    with pytest.raises(ValidationError):
        lesson.full_clean()
    lesson.refresh_from_db()
    data = {
        "capitulo": chapter.pk,
        "slug": "draft-lesson",
        "orden": 4,
        "titulo": "Borrador",
        "objetivos": "Leer",
        "minutos": 5,
        "secciones": "[]",
        "comprension": "{}",
        "resumen": "Resumen",
        "evidencia": "agronomica",
        "estado": "borrador",
    }
    form = LessonAdminForm(data=data)
    assert form.is_valid(), form.errors
    data["estado"] = "publicado"
    assert not LessonAdminForm(data=data).is_valid()
    finish_reading(client, chapter)
    attempt = start(client, chapter)
    submit(client, attempt)
    route = RutaEducativa.objects.get()
    extra = Competencia.objects.create(
        slug="otra", nombre="Otra", descripcion="Requisito nuevo",
    )
    route.requisitos.add(extra)
    assert not route_status(user, route)["eligible"]
    assert client.post(reverse("lms_route", args=[route.slug])).status_code == 403


def test_real_cultivation_and_botanical_info_do_not_require_training(client, pilot):
    user, other, chapter = pilot
    assert client.get(reverse("learning_plant", args=["romero"])).status_code == 200
    assert client.get(reverse("seguimiento:crear")).status_code == 200
    response = client.post(
        reverse("seguimiento:crear"),
        {
            "titulo": "Mi romero existente",
            "planta": "romero",
            "inicio": timezone.localdate(),
            "espacio": "Maceta",
            "objetivo": "Registrar lo que observo",
        },
    )
    assert response.status_code == 302
    assert Practica.objects.get().participante == user
    assert not CompetenciaAdquirida.objects.exists()


def test_admin_create_chapter_lesson_and_audited_publication(
    client, pilot, django_user_model,
):
    from django.contrib.admin.sites import site
    from django.test import RequestFactory

    user, other, chapter = pilot
    admin = django_user_model.objects.create_superuser(
        email="editor@example.com", password="testing-only",
    )
    client.force_login(admin)
    assert (
        client.get(reverse("admin:aprendizaje_leccioneducativa_changelist")).status_code
        == 200
    )
    response = client.post(
        reverse("admin:aprendizaje_capituloeducativo_add"),
        {
            "bloque": chapter.bloque_id,
            "numero": 25,
            "slug": "capitulo-editor",
            "titulo": "Contenido del editor",
            "descripcion": "Piloto",
            "estado": "borrador",
            "_save": "Guardar",
        },
    )
    assert response.status_code == 302
    created = CapituloEducativo.objects.get(slug="capitulo-editor")
    import json

    template = chapter.lecciones.first()
    response = client.post(
        reverse("admin:aprendizaje_leccioneducativa_add"),
        {
            "capitulo": created.pk,
            "slug": "leccion-editor",
            "orden": 1,
            "titulo": "Lección del editor",
            "objetivos": "Comprender",
            "minutos": 5,
            "secciones": json.dumps(template.secciones),
            "comprension": json.dumps(template.comprension),
            "resumen": "Resumen",
            "fuentes": [template.fuentes.first().pk],
            "evidencia": "agronomica",
            "estado": "piloto",
            "revisada": "2026-10-28",
            "nota_editorial": "Piloto",
            "_save": "Guardar",
        },
    )
    assert response.status_code == 302
    lesson = LeccionEducativa.objects.get(slug="leccion-editor")
    assert lesson.historial.get().actor == admin
    assert lesson.historial.get().contenido["fuentes"]
    assert not site._registry[IntentoCapitulo].has_change_permission(
        RequestFactory().get("/"),
    )


def test_home_shows_new_modules_and_preserves_legacy_history(client,pilot):
    user,other,chapter=pilot
    from huertos_medicinales.aprendizaje.catalogo import LECCIONES
    from huertos_medicinales.aprendizaje.models import Logro
    for item in LECCIONES: Logro.objects.create(user=user,leccion=item["slug"],xp=25)
    response=client.get(reverse("learning"))
    assert len(response.context["blocks"])==6
    assert response.context["progress"]==0
    assert response.context["total_count"]==3
    html=response.content.decode()
    assert "Recorrido inicial anterior" not in html
    assert "Conoce tu espacio" not in html
    for block in response.context["blocks"]:
        assert block.titulo in html
        detail=client.get(reverse("lms_block",args=[block.pk]))
        assert detail.status_code==200
        assert all(c.titulo in detail.content.decode() for c in block.capitulos.all())
    assert Logro.objects.filter(user=user).count()==6
    finish_reading(client,chapter)
    assert client.get(reverse("learning")).context["progress"]==100
    client.force_login(other)
    assert client.get(reverse("learning")).context["progress"]==0
