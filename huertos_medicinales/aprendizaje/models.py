from django.conf import settings
from django.db import models


class Logro(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    leccion = models.SlugField(max_length=80)
    xp = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "leccion"],
                name="unique_user_lesson_xp",
            ),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.leccion}: {self.xp} XP"


class IntentoEvaluacion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    leccion = models.SlugField(max_length=80)
    respuesta = models.CharField(max_length=8)
    resultado = models.CharField(max_length=20)
    version_contenido = models.CharField(max_length=64)
    contenido = models.JSONField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        indexes = [models.Index(fields=["user", "leccion"])]

    def __str__(self):
        return f"{self.leccion}: {self.resultado}"

# Database-backed curriculum; legacy achievements remain intact.
