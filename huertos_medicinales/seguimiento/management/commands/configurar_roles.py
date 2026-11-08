from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Configura grupos de facilitadores y gestores, sin asignar usuarios."

    def handle(self, *args, **options):
        for name, app, codes in [
            ("Gestores de privacidad", "privacidad", ["gestionar_derechos"]),
            ("Facilitadores", "seguimiento", ["revisar_practica"]),
            (
                "Gestores de comunidades",
                "comunidades",
                ["view_comunidad", "view_eventocomunidad", "publicar_comunidad"],
            ),
        ]:
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.add(
                *Permission.objects.filter(
                    content_type__app_label=app,
                    codename__in=codes,
                ),
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Grupos configurados. No se modificaron permisos de usuarios.",
            ),
        )
