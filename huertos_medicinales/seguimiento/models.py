import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from huertos_medicinales.aprendizaje.catalogo import PLANTAS


class Jardin(models.Model):
    clima = models.JSONField(default=dict, blank=True, verbose_name="Localidad y entorno del jardín")
    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    nombre = models.CharField("Nombre del jardín", max_length=80)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado", "pk"]

    def __str__(self):
        return self.nombre


class Practica(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "activa", "En seguimiento"
        FINALIZADA = "finalizada", "Finalizada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    titulo = models.CharField("Nombre de la práctica", max_length=120)
    planta = models.CharField("Planta cultivada", max_length=100)
    inicio = models.DateField("Fecha de inicio")
    espacio = models.CharField(
        "Lugar de cultivo",
        max_length=160,
        help_text="Por ejemplo: maceta junto a la ventana. No incluyas tu dirección.",
    )
    objetivo = models.TextField("Qué quieres observar", max_length=1500)
    estado = models.CharField(max_length=16, choices=Estado, default=Estado.ACTIVA)
    dias_adelanto = models.PositiveIntegerField(
        "Días de adelanto (solo administración)",
        default=0,
        help_text=(
            "Uso exclusivo de administración para demostraciones. No cambia la "
            "fecha real de inicio ni las observaciones registradas."
        ),
    )
    jardin = models.ForeignKey(Jardin, on_delete=models.PROTECT, null=True, blank=True, related_name="cultivos")
    posicion = models.PositiveSmallIntegerField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["jardin", "posicion"], name="unique_garden_slot"),
            models.CheckConstraint(condition=(models.Q(jardin__isnull=True, posicion__isnull=True) | models.Q(jardin__isnull=False, posicion__gte=1, posicion__lte=6, posicion__isnull=False)), name="garden_slot_valid"),
        ]
        ordering = ["-creada"]
        permissions = [
            ("revisar_practica", "Acompañar prácticas y escribir devoluciones"),
            (
                "avanzar_tiempo_practica",
                "Adelantar el tiempo de una práctica (demostraciones)",
            ),
        ]
        indexes = [models.Index(fields=["participante", "estado"])]

    def __str__(self):
        return self.titulo

    @property
    def info_planta(self):
        return next((item for item in PLANTAS if item["slug"] == self.planta), None)

    @property
    def imagen_jardin(self):
        if self.info_planta:
            return f"images/huertos/plantas/{self.planta}-sprite.png"
        return "images/huertos/maceta.svg"

    @property
    def imagen_referencia(self):
        if self.info_planta:
            return f"images/huertos/plantas/{self.planta}.png"
        return "images/huertos/maceta.svg"

    @property
    def planta_nombre(self):
        info = self.info_planta
        return info["nombre"] if info else self.planta

    @property
    def dias_transcurridos(self):
        return max(0, (timezone.localdate() - self.inicio).days) + self.dias_adelanto

    @property
    def etapa(self):
        info = self.info_planta
        if not info:
            return None
        dias = self.dias_transcurridos
        if dias < info["dias_germinacion"]:
            return "semilla"
        if dias < info["dias_madurez"]:
            return "creciendo"
        return "madura"


class Observacion(models.Model):
    practica = models.ForeignKey(
        Practica,
        on_delete=models.PROTECT,
        related_name="observaciones",
    )
    fecha = models.DateField("Fecha de la observación")
    accion = models.TextField("Qué hiciste", max_length=1500)
    resultado = models.TextField("Qué observaste", max_length=2000)
    pregunta = models.TextField("Dudas o dificultades", max_length=1000, blank=True)
    foto = models.ImageField(
        "Foto de la siembra",
        upload_to="seguimiento/fotos/%Y/%m/",
        blank=True,
        null=True,
        help_text="Opcional. Una foto que muestre el estado real de tu siembra.",
    )
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-creada"]

    def __str__(self):
        return f"{self.practica}: {self.fecha}"


class Devolucion(models.Model):
    practica = models.ForeignKey(
        Practica,
        on_delete=models.PROTECT,
        related_name="devoluciones",
    )
    facilitador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    texto = models.TextField("Orientación para el participante", max_length=2000)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada"]

    def __str__(self):
        return f"Orientación: {self.practica_id}"


class EventoPractica(models.Model):
    practica = models.ForeignKey(
        Practica,
        on_delete=models.PROTECT,
        related_name="eventos",
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    accion = models.CharField(max_length=40)
    detalle = models.JSONField(default=dict)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.accion}: {self.practica_id}"


class ActividadCalendario(models.Model):
    TIPOS = [("riego", "Riego"), ("revision", "Revisión"), ("foto", "Fotografía"), ("poda", "Poda"), ("cosecha", "Cosecha"), ("otro", "Otro cuidado")]
    practica = models.ForeignKey(Practica, on_delete=models.PROTECT, related_name="actividades_calendario")
    tipo = models.CharField("Actividad", max_length=16, choices=TIPOS)
    fecha = models.DateField("Fecha")
    hora = models.TimeField("Hora", blank=True, null=True)
    notas = models.TextField("Indicaciones", max_length=1500, blank=True)
    completada = models.BooleanField(default=False)
    completada_en = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.practica} · {self.fecha}"

    class Meta:
        ordering = ["fecha", "hora", "pk"]
