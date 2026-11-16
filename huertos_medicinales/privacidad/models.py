import uuid

from django.conf import settings
from django.db import models


class PreferenciaCookies(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    version = models.CharField(max_length=24)
    mapas_externos = models.BooleanField(default=False)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada"]

    def __str__(self):
        return f"{self.version}: mapas={self.mapas_externos}"


class AceptacionCondiciones(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    version = models.CharField(max_length=24)
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Condiciones {self.version}: {self.usuario_id}"
