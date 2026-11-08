"""Carga editorial conservadora: no modifica lecciones existentes ni su progreso."""
import json
from datetime import date
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max

from huertos_medicinales.aprendizaje.educational_models import CapituloEducativo
from huertos_medicinales.aprendizaje.educational_models import Competencia
from huertos_medicinales.aprendizaje.educational_models import EvaluacionEducativa
from huertos_medicinales.aprendizaje.educational_models import FuenteEducativa
from huertos_medicinales.aprendizaje.educational_models import LeccionEducativa


def question(text, choices, correct, explanation, slug, kind="unica"):
    return dict(enunciado=text, opciones=choices, correctas=correct, explicacion=explanation,
                tipo=kind, dificultad="inicial", competencia=slug)

class Command(BaseCommand):
    help = "Añade contenido documental e interactivo a los 24 capítulos sin reiniciar avances."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_education_pilot", verbosity=0)
        document = json.loads((Path(__file__).resolve().parents[2]/"data"/"curriculum.json").read_text(encoding="utf-8"))
        count = 0
        for entry in document["chapters"]:
            chapter = CapituloEducativo.objects.get(numero=entry["numero"])
            slug = f"capitulo-{chapter.numero}-contenido"
            if LeccionEducativa.objects.filter(slug=slug).exists():
                continue  # Nunca sobrescribe edición, archivo o revisión del administrador.
            if chapter.estado == "archivado":
                self.stdout.write(f"Capítulo {chapter.numero} archivado: se conserva.")
                continue
            comp_slug = f"fundamentos-capitulo-{chapter.numero}"
            competency, _ = Competencia.objects.get_or_create(slug=comp_slug, defaults={
                "nombre": chapter.titulo,
                "descripcion": "Comprensión inicial de conceptos y decisiones del capítulo; no certificación profesional.",
            })
            sections = entry["secciones"]
            image = entry["imagen"]
            if image in {"manzanilla", "menta", "calendula", "romero"}:
                image_path = f"images/huertos/plantas/{image}.png"
                caption = f"Ilustración botánica de {image}; no es una foto del cultivo del participante."
            else:
                image_path = f"images/educacion/capitulo-{chapter.numero}.svg"
                caption = "Esquema didáctico original. Representa conceptos, no medidas ni un diagnóstico."
            sections[0].update(imagen=image_path, imagen_alt=f"Esquema de {chapter.titulo}", pie=caption)
            sections[1]["explorar"] = [dict(titulo=s["titulo"], texto=s["texto"]) for s in sections[:3]]
            sections[2]["caso"] = dict(titulo=entry["caso"], opciones=[
                dict(texto=choice, respuesta=("Buena decisión. " if i == 0 else "Revisa esta decisión. ")+entry["explicacion"])
                for i,choice in enumerate(entry["opciones"])])
            sections[3]["practica"] = entry["practica"]
            if chapter.numero == 11:
                sections[3]["calculadora"] = True
            choices = entry["opciones"][:]
            offset = chapter.numero % len(choices)
            choices = choices[offset:] + choices[:offset]
            correct_index = (len(choices)-offset) % len(choices)
            questions = [
                question(entry["caso"], choices, [correct_index], entry["explicacion"], comp_slug),
                question(entry["verdadero"], ["Verdadero", "Falso"], [0], entry["verdadero"], comp_slug, "booleano"),
                question(entry["falso"], ["Verdadero", "Falso"], [1], "La afirmación generaliza de forma incorrecta. Revisa las condiciones y distinciones del capítulo.", comp_slug, "booleano"),
            ]
            order = (chapter.lecciones.aggregate(value=Max("orden"))["value"] or 0) + 1
            lesson = LeccionEducativa(capitulo=chapter, slug=slug, orden=order,
                titulo=chapter.titulo + ": comprende y aplica", objetivos=f"Comprender {chapter.titulo.lower()}, analizar un caso y preparar una observación propia.",
                minutos=8, secciones=sections, comprension=questions[0], resumen=entry["verdadero"]+" "+entry["explicacion"],
                estado="publicado", revisada=date(2026,10,29),
                evidencia="cientifica" if chapter.numero in {1,2,3,8,15,22} else "agronomica",
                nota_editorial="Síntesis educativa con revisión documental. Actividades y esquemas originales. Las recomendaciones se contextualizan por especie y lugar; no implica validación agronómica local ni asesoramiento médico.")
            lesson.full_clean();lesson.save()
            for key in entry["fuentes"]:
                title,institution,url=document["sources"][key]
                source,_=FuenteEducativa.objects.get_or_create(url=url,defaults=dict(titulo=title,institucion=institution,consultada=date(2026,10,29)))
                lesson.fuentes.add(source)
            # La revisión guarda también las referencias que acompañan a esta versión.
            revision=lesson.historial.get(numero=lesson.revision)
            revision.contenido["fuentes"]=list(lesson.fuentes.values("titulo","url","institucion","consultada"))
            for source in revision.contenido["fuentes"]:
                source["consultada"]=str(source["consultada"])
            revision.save(update_fields=["contenido"])
            exam, created=EvaluacionEducativa.objects.get_or_create(capitulo=chapter, defaults=dict(titulo="Evaluación: "+chapter.titulo,preguntas=questions,porcentaje_minimo=80,estado="publicado"))
            if not created:
                # El capítulo 5 conserva preguntas y competencias del piloto y suma las nuevas.
                exam.preguntas=exam.preguntas+questions
            exam.competencias.add(competency)
            exam.full_clean();exam.save()
            chapter.estado="publicado"
            chapter.descripcion="Cuatro secciones ilustradas, exploración de conceptos, caso práctico y evaluación."
            chapter.save(update_fields=["estado","descripcion"])
            count+=1
        self.stdout.write(self.style.SUCCESS(f"{count} lecciones nuevas. Avances e historial conservados."))
