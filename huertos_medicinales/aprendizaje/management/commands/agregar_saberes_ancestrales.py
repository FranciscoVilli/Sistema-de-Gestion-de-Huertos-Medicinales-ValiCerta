"""Agrega conocimiento ancestral (ritual de siembra, bano y gratitud antes de
la cosecha) a las lecciones ya publicadas de calendario lunar y cosecha, sin
tocar nada mas del capitulo. Idempotente: no duplica si ya se agrego."""
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from huertos_medicinales.aprendizaje.educational_models import CapituloEducativo
from huertos_medicinales.aprendizaje.educational_models import FuenteEducativa

FUENTE_MSP_RITUAL = (
    "MSP Ecuador (2017), Lineamientos de huertos medicinales, p. 42-47",
    "Ministerio de Salud Pública del Ecuador",
    "https://www.salud.gob.ec/wp-content/uploads/2022/09/"
    "MSP-Lineamientos-implementaci%D0%B2n-huertos-medicinales-PNA-2017-2.pdf",
)

SECCIONES_NUEVAS = {
    15: {
        "titulo": "El ritual de siembra",
        "texto": (
            "Más allá de elegir el día según la fase lunar, varias comunidades practican un "
            "ritual de siembra: se realiza al amanecer, en fase de luna creciente o luna "
            "llena, como un momento de intención y conexión con el huerto antes de poner la "
            "semilla en la tierra. El Ministerio de Salud Pública del Ecuador documenta esta "
            "práctica como parte del conocimiento ancestral de huertos medicinales (MSP "
            "Ecuador, 2017, Lineamientos de huertos medicinales, p. 42-47). Seguir este "
            "ritual —elegir la hora, preparar el ánimo, agradecer antes de sembrar— es una "
            "decisión cultural y personal, no un paso que cambie por sí mismo la germinación "
            "o el rendimiento de la planta. Si tu comunidad tiene esta tradición, regístrala "
            "en tus actividades como lo que es: una práctica con valor cultural propio, "
            "además de —no en lugar de— verificar las condiciones reales de luz, agua y "
            "sustrato que tu planta necesita."
        ),
    },
    20: {
        "titulo": "Baño y gratitud antes de cosechar",
        "texto": (
            "Algunas comunidades acompañan la cosecha con dos prácticas ancestrales "
            "adicionales: un baño de las plantas dos días antes de cosechar —cuya duración "
            "exacta varía si la especie es de ciclo corto o largo— y un ritual de gratitud "
            "al amanecer, previo a la recolección, como forma de reconocer lo que la tierra "
            "y la planta han dado. El Ministerio de Salud Pública del Ecuador recoge estas "
            "prácticas dentro de los lineamientos de huertos medicinales con enfoque "
            "intercultural (MSP Ecuador, 2017, Lineamientos de huertos medicinales, p. "
            "42-47). Como con el ritual de siembra, esto es conocimiento cultural que puedes "
            "elegir mantener junto a tu comunidad; no sustituye los criterios de madurez y "
            "las señales de la propia planta que ya viste en las secciones anteriores para "
            "decidir cuándo y qué parte cosechar."
        ),
    },
}


class Command(BaseCommand):
    help = (
        "Agrega el ritual de siembra y el bano/gratitud antes de cosechar a las "
        "lecciones existentes de calendario lunar y cosecha."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        titulo, institucion, url = FUENTE_MSP_RITUAL
        fuente, _ = FuenteEducativa.objects.get_or_create(
            url=url,
            defaults={"titulo": titulo, "institucion": institucion, "consultada": date.today()},
        )
        for numero, seccion in SECCIONES_NUEVAS.items():
            try:
                capitulo = CapituloEducativo.objects.get(numero=numero)
            except CapituloEducativo.DoesNotExist:
                self.stdout.write(f"Capítulo {numero} no existe todavía; omitido.")
                continue
            leccion = capitulo.lecciones.filter(slug=f"capitulo-{numero}-contenido").first()
            if leccion is None:
                self.stdout.write(f"Lección de capítulo {numero} no existe todavía; omitido.")
                continue
            if any(s.get("titulo") == seccion["titulo"] for s in leccion.secciones):
                self.stdout.write(f"Capítulo {numero}: ya tiene esta sección, se conserva.")
                continue
            leccion.secciones = [*leccion.secciones, seccion]
            leccion.full_clean()
            leccion.save()
            leccion.fuentes.add(fuente)
            self.stdout.write(self.style.SUCCESS(f"Capítulo {numero}: sección agregada."))
