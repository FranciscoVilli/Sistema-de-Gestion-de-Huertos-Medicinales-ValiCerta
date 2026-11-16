"""Vincula cada planta del catálogo a un capítulo del temario de 24 capítulos.

No modifica ni archiva la ruta piloto de manzanilla (Capítulo 5): esta
solo añade una ruta adicional, más temprana, para que el Módulo 1
también la desbloquee. Idempotente: no duplica rutas en ejecuciones repetidas.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from huertos_medicinales.aprendizaje.educational_models import CapituloEducativo
from huertos_medicinales.aprendizaje.educational_models import RutaEducativa

PLAN = [
    ("manzanilla-fundamentos", "Manzanilla: desde los fundamentos", "manzanilla", 1),
    ("menta-siembra-propagacion", "Menta: siembra y propagación", "menta", 11),
    ("calendula-sanidad-vegetal", "Caléndula: sanidad y protección", "calendula", 16),
    ("romero-cosecha", "Romero: cosecha y aprovechamiento", "romero", 20),
]


class Command(BaseCommand):
    help = "Crea una ruta educativa por planta, repartidas a lo largo del temario."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_curriculum", verbosity=0)
        count = 0
        for slug, nombre, especie, numero in PLAN:
            chapter = CapituloEducativo.objects.get(numero=numero)
            competency = chapter.evaluacion.competencias.get(
                slug=f"fundamentos-capitulo-{numero}",
            )
            route, created = RutaEducativa.objects.get_or_create(
                slug=slug,
                defaults={
                    "nombre": nombre,
                    "especie": especie,
                    "estado": "piloto",
                    "descripcion": (
                        f"Se desbloquea al aprobar el Capítulo {numero} "
                        f"({chapter.titulo})."
                    ),
                },
            )
            route.requisitos.set([competency])
            count += created
        self.stdout.write(
            self.style.SUCCESS(
                f"{count} rutas nuevas por planta. Existentes conservadas.",
            ),
        )
