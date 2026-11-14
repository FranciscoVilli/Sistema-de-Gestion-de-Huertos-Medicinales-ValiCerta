
import random
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.db.models import EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for Huertos Medicinales Comunitarios.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    class Genero(models.TextChoices):
        FEMENINO = "femenino", "Femenino"
        MASCULINO = "masculino", "Masculino"
        OTRO = "otro", "Otro"
        PREFIERE_NO_DECIR = "prefiere_no_decir", "Prefiere no decir"

    # First and last name do not cover name patterns around the globe
    name = CharField("Nombre completo", blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    foto = models.ImageField(
        "Foto de perfil",
        upload_to="perfiles/%Y/%m/",
        blank=True,
        null=True,
    )
    fecha_nacimiento = models.DateField("Fecha de nacimiento", null=True, blank=True)
    genero = models.CharField("Género", max_length=20, choices=Genero, blank=True)
    telefono = models.CharField("Número de teléfono", max_length=20, blank=True)
    direccion = models.CharField(
        "Dirección de domicilio",
        max_length=200,
        blank=True,
        help_text="Uso interno; no se muestra públicamente.",
    )
    talentos = models.CharField(
        "Talentos o habilidades",
        max_length=300,
        blank=True,
        help_text="Opcional. Sepáralos por coma; una comunidad puede certificarlos luego.",
    )
    codigo_unico = models.CharField(
        "Código único de identificación",
        max_length=6,
        unique=True,
        editable=False,
        null=True,
        blank=True,
        help_text="Código de 6 dígitos para que una comunidad pueda agregarte como miembro.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def save(self, *args, **kwargs):
        if not self.codigo_unico:
            self.codigo_unico = self._generar_codigo_unico()
        super().save(*args, **kwargs)

    @classmethod
    def _generar_codigo_unico(cls) -> str:
        while True:
            codigo = f"{random.randint(0, 999999):06d}"
            if not cls.objects.filter(codigo_unico=codigo).exists():
                return codigo

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})
