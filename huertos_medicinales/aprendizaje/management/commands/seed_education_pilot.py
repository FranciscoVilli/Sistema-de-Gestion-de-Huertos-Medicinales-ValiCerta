from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from huertos_medicinales.aprendizaje.educational_models import BloqueEducativo
from huertos_medicinales.aprendizaje.educational_models import CapituloEducativo
from huertos_medicinales.aprendizaje.educational_models import Competencia
from huertos_medicinales.aprendizaje.educational_models import EvaluacionEducativa
from huertos_medicinales.aprendizaje.educational_models import FuenteEducativa
from huertos_medicinales.aprendizaje.educational_models import LeccionEducativa
from huertos_medicinales.aprendizaje.educational_models import RutaEducativa

BLOCKS = [
    (
        "Fundamentos de las plantas",
        [
            "Introducción a las plantas medicinales",
            "Botánica básica",
            "Ciclo de vida de las plantas",
            "Tipos de huertos",
        ],
    ),
    (
        "Condiciones para cultivar",
        [
            "Suelos y sustratos",
            "Nutrientes y fertilización",
            "Agua y riego",
            "Luz y fotosíntesis",
            "Clima y condiciones ambientales",
            "Preparación del huerto",
        ],
    ),
    (
        "Siembra y desarrollo",
        [
            "Semillas y germinación",
            "Siembra y propagación",
            "Trasplante",
            "Mantenimiento",
            "Calendario agrícola y ciclos lunares",
        ],
    ),
    (
        "Sanidad y protección vegetal",
        [
            "Plagas e insectos",
            "Hongos y enfermedades",
            "Diagnóstico de problemas",
            "Manejo integrado y prevención",
        ],
    ),
    (
        "Cosecha y aprovechamiento",
        ["Cosecha", "Secado y conservación", "Usos y seguridad de plantas medicinales"],
    ),
    ("Sostenibilidad y seguimiento", ["Cultivo ecológico", "Seguimiento del cultivo"]),
]
SOURCES = [
    (
        "El medio de cultivo en recipientes",
        "University of Maryland Extension",
        "https://extension.umd.edu/resource/growing-media-potting-soil-containers",
    ),
    (
        "Suelo de jardín y mezclas para macetas",
        "Iowa State University Extension",
        "https://yardandgarden.extension.iastate.edu/faq/i-would-grow-few-vegetables-containers-can-i-use-garden-soil-or-should-i-purchase-commercial",
    ),
    (
        "Recipientes y sustratos",
        "University of Illinois Extension",
        "https://extension.illinois.edu/houseplants/get-started",
    ),
]


def q(text, options, answers, explanation, kind="unica"):
    return {
        "enunciado": text,
        "opciones": options,
        "correctas": answers,
        "explicacion": explanation,
        "tipo": kind,
        "dificultad": "inicial",
        "competencia": "sustrato-observacion",
    }


QUESTIONS = [
    q(
        "¿Qué funciones cumple el sustrato?",
        [
            "Sostener la planta y permitir el acceso de las raíces a aire y agua",
            "Reemplazar la luz",
            "Evitar cualquier intercambio de agua",
        ],
        [0],
        "El medio de cultivo sostiene la planta y participa en el suministro de aire, agua y nutrientes.",
    ),
    q(
        "El suelo de jardín se comporta siempre igual en una maceta.",
        ["Verdadero", "Falso"],
        [1],
        "En un recipiente puede compactarse y dificultar la aireación y el drenaje.",
        "booleano",
    ),
    q(
        "¿Qué conviene revisar al elegir un recipiente y su mezcla?",
        [
            "La salida de agua",
            "Las necesidades de la especie",
            "Solo el color del recipiente",
        ],
        [0, 1],
        "La selección debe considerar drenaje y necesidades de la planta; la apariencia no basta.",
        "multiple",
    ),
]
LESSONS = [
    (
        "sustrato-funciones",
        "¿Qué hace el sustrato?",
        "Reconocer funciones del medio de cultivo.",
        [
            {
                "titulo": "Un entorno para las raíces",
                "texto": "En una maceta, las raíces ocupan un volumen limitado. El medio de cultivo sostiene la planta y permite el acceso a agua, aire y nutrientes. Por eso su elección importa.",
            },
            {
                "titulo": "Espacios entre partículas",
                "texto": "Los espacios del sustrato permiten el movimiento de aire y agua. Si el agua sobrante no puede salir, se dificulta la entrada de aire. La apariencia superficial no describe todo lo que sucede alrededor de las raíces.",
            },
        ],
        "El sustrato es parte del entorno de las raíces, no solo un soporte.",
        0,
    ),
    (
        "suelo-y-maceta",
        "Suelo de jardín y mezclas para maceta",
        "Distinguir el contexto de cultivo en suelo y en recipiente.",
        [
            {
                "titulo": "El recipiente cambia el contexto",
                "texto": "El suelo tomado del jardín puede compactarse en una maceta. Esto puede dificultar el drenaje y la aireación. No conviene asumir que un material funcionará igual en cualquier espacio.",
            },
            {
                "titulo": "Comparar antes de elegir",
                "texto": "Las mezclas comerciales tienen distintas cualidades. Consulta su composición y uso indicado. Una mezcla para recipientes debe permitir drenaje y retener humedad; una etiqueta o un precio por sí solos no garantizan que sea adecuada para tu especie.",
            },
        ],
        "Compara el uso indicado y las características de la mezcla antes de elegir.",
        1,
    ),
    (
        "revisar-drenaje",
        "Revisar recipiente y drenaje",
        "Identificar qué observar antes de preparar una maceta.",
        [
            {
                "titulo": "Revisar la salida de agua",
                "texto": "Para la mayoría de las plantas en maceta, un recipiente con drenaje adecuado reduce los problemas asociados al encharcamiento. Comprueba la salida de agua y consulta las necesidades de la especie antes de preparar el cultivo.",
            },
            {
                "titulo": "Tu observación inicial",
                "texto": "Observa un recipiente vacío y anota si tiene salida de agua, qué mezcla piensas usar y qué información te falta consultar. No necesitas sembrar ni modificar una planta para realizar este ejercicio. Es una actividad de reconocimiento, no una prueba de que todas las condiciones sean adecuadas.",
            },
        ],
        "Anota lo observado y lo que todavía necesitas verificar para tu especie.",
        2,
    ),
]


class Command(BaseCommand):
    help = "Crea estructura y piloto revisable sin sobrescribir contenidos existentes."

    @transaction.atomic
    def handle(self, *args, **options):
        number = 0
        for i, (title, chapters) in enumerate(BLOCKS, 1):
            block, _ = BloqueEducativo.objects.get_or_create(
                numero=i, defaults={"titulo": title},
            )
            for title in chapters:
                number += 1
                CapituloEducativo.objects.get_or_create(
                    numero=number,
                    defaults={
                        "bloque": block,
                        "slug": slugify(title),
                        "titulo": title,
                        "estado": "piloto" if number == 5 else "borrador",
                        "descripcion": "Contenido piloto revisable: lectura, comprensión y evaluación."
                        if number == 5
                        else "Estructura editorial. Contenido pendiente de revisión y publicación.",
                    },
                )
        chapter = CapituloEducativo.objects.get(numero=5)
        sources = []
        for title, institution, url in SOURCES:
            source, _ = FuenteEducativa.objects.get_or_create(
                url=url,
                defaults={
                    "titulo": title,
                    "institucion": institution,
                    "consultada": date(2026, 10, 28),
                },
            )
            sources.append(source)
        lessons = []
        for order, (slug, title, objectives, sections, summary, index) in enumerate(
            LESSONS, 1,
        ):
            lesson, created = LeccionEducativa.objects.get_or_create(
                slug=slug,
                defaults={
                    "capitulo": chapter,
                    "orden": order,
                    "titulo": title,
                    "objetivos": objectives,
                    "secciones": sections,
                    "comprension": QUESTIONS[index],
                    "resumen": summary,
                    "minutos": 4,
                    "revisada": date(2026, 10, 28),
                    "estado": "borrador",
                    "nota_editorial": "Piloto educativo. Fuentes documentales consultadas; pendiente de revisión pedagógica y agronómica local. No es una receta de sustrato por especie.",
                },
            )
            if created:
                lesson.fuentes.add(sources[index])
                lesson.estado = "piloto"
                lesson.full_clean()
                lesson.save()
            lessons.append(lesson)
        competency, _ = Competencia.objects.get_or_create(
            slug="sustrato-observacion",
            defaults={
                "nombre": "Reconocimiento inicial de sustrato y drenaje",
                "descripcion": "Distingue funciones del medio de cultivo y criterios iniciales de observación de recipientes. Competencia piloto, no certificación profesional.",
            },
        )
        exam, created = EvaluacionEducativa.objects.get_or_create(
            capitulo=chapter,
            defaults={
                "titulo": "Comprueba lo aprendido: suelos y sustratos",
                "preguntas": QUESTIONS,
                "porcentaje_minimo": 80,
                "estado": "piloto",
            },
        )
        if created:
            exam.competencias.add(competency)
        route, created = RutaEducativa.objects.get_or_create(
            slug="manzanilla-observar-recipiente",
            defaults={
                "nombre": "Manzanilla: observar mi recipiente (piloto)",
                "especie": "manzanilla",
                "descripcion": "Primer ejercicio guiado de observación. No equivale a una ruta completa de cultivo de manzanilla.",
                "instrucciones": "1. Consulta la ficha de manzanilla.\n2. Observa el recipiente vacío y su salida de agua.\n3. Anota qué sustrato considerarías y qué información necesitas verificar.\n4. Si ya tienes un cultivo, guarda la observación en su bitácora. No necesitas crear otro cultivo ni cambiar el existente.",
                "estado": "piloto",
            },
        )
        if created:
            route.requisitos.add(competency)
            route.lecciones.add(*lessons)
        self.stdout.write(
            self.style.SUCCESS(
                "Estructura: 6 bloques, 24 capítulos. Piloto: 3 lecciones, evaluación y ruta. Datos anteriores conservados.",
            ),
        )
