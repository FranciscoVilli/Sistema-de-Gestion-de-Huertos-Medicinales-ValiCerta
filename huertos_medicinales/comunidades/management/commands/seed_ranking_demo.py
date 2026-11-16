from datetime import date
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone

from huertos_medicinales.comunidades.models import Comunidad
from huertos_medicinales.comunidades.models import Miembro
from huertos_medicinales.seguimiento.models import Observacion
from huertos_medicinales.seguimiento.models import Practica


class Command(BaseCommand):
    help = "Crea comunidades [DEMO] para visualizar el ranking, sin duplicar datos."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            msg = "Solo disponible en desarrollo (DEBUG)."
            raise CommandError(msg)
        demo_group, _ = Group.objects.get_or_create(
            name="Huertos · Ranking de demostración",
        )
        examples = [
            ("Semillas de Ibarra", "Imbabura", "Ibarra", 3, 120),
            ("Raíces compartidas", "Pichincha", "Quito", 3, 90),
            ("Huerto de mi barrio", "Azuay", "Cuenca", 2, 60),
            ("Guardianes de la menta", "Loja", "Loja", 2, 40),
            ("Primeros brotes", "Tungurahua", "Ambato", 1, 20),
        ]
        today = timezone.localdate()
        for index, (name, province, city, count, observations) in enumerate(
            examples,
            1,
        ):
            users = []
            for number in range(1, count + 1):
                user, created = get_user_model().objects.get_or_create(
                    email=f"ranking-demo-{index}-{number}@example.invalid",
                    defaults={
                        "name": f"[DEMO] Cultivador {index}.{number}",
                        "fecha_nacimiento": date(1990, 1, 1),
                        "genero": "prefiere_no_decir",
                        "telefono": "0000000000",
                        "direccion": "[DEMO] Ubicación ficticia",
                        "is_active": True,
                    },
                )
                if created:
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                user.groups.add(demo_group)
                users.append(user)
            community, _ = Comunidad.objects.get_or_create(
                responsable=users[0],
                nombre="[DEMO] " + name,
                defaults={
                    "provincia": province,
                    "localidad": city,
                    "descripcion": (
                        "Comunidad ficticia para visualizar el podio y el ranking. "
                        "Sus integrantes y registros no representan personas ni "
                        "cultivos reales."
                    ),
                    "encuentro": "Datos de demostración, sin encuentros reales.",
                    "grupo_virtual": True,
                    "estado": Comunidad.Estado.PUBLICADA,
                },
            )
            for number, user in enumerate(users):
                membership, created = Miembro.objects.get_or_create(
                    usuario=user,
                    defaults={
                        "comunidad": community,
                        "fecha_nacimiento": date(1990, 1, 1),
                        "estado": Miembro.Estado.APROBADA,
                    },
                )
                if membership.comunidad_id != community.pk:
                    msg = (
                        "Un usuario reservado de demostración pertenece a otra "
                        "comunidad; no se modificó."
                    )
                    raise CommandError(
                        msg,
                    )
                crop, _ = Practica.objects.get_or_create(
                    participante=user,
                    titulo=f"[DEMO RANKING {index}.{number + 1}] Menta",
                    defaults={
                        "planta": "menta",
                        "inicio": today - timedelta(days=60),
                        "espacio": "[DEMO] Maceta ficticia",
                        "objetivo": (
                            "Registros de prueba para visualizar XP comunitarios."
                        ),
                    },
                )
                total = observations // count + (
                    1 if number < observations % count else 0
                )
                for n in range(total):
                    Observacion.objects.get_or_create(
                        practica=crop,
                        accion=f"[DEMO RANKING] Observación de ejemplo {n + 1}",
                        defaults={
                            "fecha": today - timedelta(days=total - n),
                            "resultado": (
                                "Registro ficticio para comprobar la clasificación. No "
                                "corresponde a una observación real."
                            ),
                        },
                    )
            self.stdout.write(
                f"{community.nombre}: {community.puntos} XP · {count} integrantes",
            )
        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Ranking de demostración preparado. Los datos existentes se "
                    "conservaron."
                ),
            ),
        )
