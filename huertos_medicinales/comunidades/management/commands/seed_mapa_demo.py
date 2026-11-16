from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from huertos_medicinales.comunidades.models import Comunidad
from huertos_medicinales.comunidades.models import JardinCompartido
from huertos_medicinales.comunidades.models import Miembro
from huertos_medicinales.comunidades.models import PerfilComunitario
from huertos_medicinales.seguimiento.models import Jardin


class Command(BaseCommand):
    help = (
        "Crea comunidades [DEMO] con integrantes y jardines visibles "
        "para probar los colores del mapa, sin duplicar datos."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            msg = "Solo disponible en desarrollo (DEBUG)."
            raise CommandError(msg)
        demo_group, _ = Group.objects.get_or_create(
            name="Huertos · Mapa de demostración",
        )
        examples = [
            (
                "Semillas del valle",
                "Manabí",
                "Manta",
                [("Mateo", -0.95, -80.73), ("Sofía", -0.97, -80.70)],
            ),
            (
                "Raíces del sur",
                "Loja",
                "Loja",
                [("Renata", -3.99, -79.20), ("Iván", -4.01, -79.22)],
            ),
            (
                "Huerto andino",
                "Napo",
                "Tena",
                [("Camila", -0.98, -77.80), ("Bruno", -1.00, -77.82)],
            ),
        ]
        for index, (name, province, city, members) in enumerate(examples, 1):
            users = []
            for number, (persona, _lat, _lon) in enumerate(members, 1):
                user, created = get_user_model().objects.get_or_create(
                    email=f"mapa-demo-{index}-{number}@example.invalid",
                    defaults={
                        "name": f"[DEMO] {persona}",
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
                        "Comunidad ficticia para visualizar los colores del mapa. Sus "
                        "integrantes y jardines no son reales."
                    ),
                    "encuentro": "Datos de demostración, sin encuentros reales.",
                    "grupo_virtual": True,
                    "estado": Comunidad.Estado.PUBLICADA,
                },
            )
            for (persona, lat, lon), user in zip(members, users, strict=True):
                membership, _ = Miembro.objects.get_or_create(
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
                PerfilComunitario.objects.get_or_create(
                    usuario=user,
                    defaults={
                        "nombre": f"[DEMO] {persona}",
                        "visible": True,
                        "localidad": city,
                        "experiencia": (
                            "Perfil ficticio de demostración para probar los "
                            "colores del mapa."
                        ),
                    },
                )
                garden, _ = Jardin.objects.get_or_create(
                    propietario=user,
                    nombre=f"[DEMO] Jardín de {persona}",
                )
                JardinCompartido.objects.update_or_create(
                    jardin=garden,
                    defaults={
                        "visible": True,
                        "localidad": city + " · Sector de demostración",
                        "latitud": lat,
                        "longitud": lon,
                    },
                )
            self.stdout.write(
                f"{community.nombre}: {len(users)} integrantes con jardín visible",
            )
        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Mapa de demostración preparado: 3 comunidades, 6 jardines "
                    "visibles. Los datos existentes se conservaron."
                ),
            ),
        )
