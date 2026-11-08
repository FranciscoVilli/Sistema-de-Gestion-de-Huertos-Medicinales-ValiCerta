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


class SolicitudDerecho(models.Model):
    class Tipo(models.TextChoices):
        ACCESO = "acceso", "Acceso a mis datos"
        RECTIFICACION = "rectificacion", "Rectificar o actualizar datos"
        ELIMINACION = "eliminacion", "Eliminar datos"
        OPOSICION = "oposicion", "Oposición o suspensión del tratamiento"
        PORTABILIDAD = "portabilidad", "Portabilidad de mis datos"
        REVOCACION = "revocacion", "Revocar una autorización"
        OTRO = "otro", "Consulta de privacidad"

    class Estado(models.TextChoices):
        RECIBIDA = "recibida", "Recibida"
        EN_GESTION = "en_gestion", "En gestión"
        RESPONDIDA = "respondida", "Respondida"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    tipo = models.CharField("Qué deseas solicitar", max_length=24, choices=Tipo)
    detalle = models.TextField("Describe tu solicitud", max_length=3000)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada"]
        permissions = [
            ("gestionar_derechos", "Consultar y responder solicitudes de derechos"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.pk}"

    @property
    def ultimo_estado(self):
        ultimo = self.respuestas.order_by("-creada").first()
        return ultimo.get_estado_display() if ultimo else "Recibida"


class RespuestaDerecho(models.Model):
    solicitud = models.ForeignKey(
        SolicitudDerecho,
        on_delete=models.PROTECT,
        related_name="respuestas",
    )
    gestor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    estado = models.CharField(
        "Estado de gestión",
        max_length=24,
        choices=SolicitudDerecho.Estado,
    )
    texto = models.TextField("Respuesta al titular", max_length=4000)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creada"]

    def __str__(self):
        return f"{self.solicitud_id}: {self.estado}"
