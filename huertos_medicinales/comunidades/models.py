import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models


class Comunidad(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente de revisión"
        PUBLICADA = "publicada", "Publicada"
        RETIRADA = "retirada", "Retirada de publicación"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    nombre = models.CharField("Nombre de la comunidad o huerto", max_length=140)
    provincia = models.CharField("Provincia", max_length=80)
    localidad = models.CharField("Cantón o localidad", max_length=100)
    descripcion = models.TextField("Presentación de la comunidad", max_length=2000)
    encuentro = models.TextField(
        "Cómo participar o conocer los encuentros",
        max_length=1000,
        help_text=(
            "Describe un canal público o un punto comunitario. No "
            "incluyas domicilios ni datos personales de terceros."
        ),
    )
    plantas_destacadas = models.CharField(
        "Plantas que cultiva esta comunidad",
        max_length=200,
        blank=True,
        help_text=(
            "Opcional. Nombres separados por coma, por ejemplo: manzanilla, menta."
        ),
    )
    latitud = models.DecimalField(
        "Latitud aproximada",
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitud = models.DecimalField(
        "Longitud aproximada",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    estado = models.CharField(
        max_length=16,
        choices=Estado,
        default=Estado.PENDIENTE,
        db_index=True,
    )
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        permissions = [
            ("publicar_comunidad", "Revisar y publicar comunidades en el mapa"),
        ]

    def __str__(self):
        return self.nombre


class EventoComunidad(models.Model):
    comunidad = models.ForeignKey(
        Comunidad,
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
        return f"{self.accion}: {self.comunidad_id}"


class PerfilComunitario(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil_comunitario")
    nombre = models.CharField("Nombre público", max_length=80)
    nivel = models.CharField("Experiencia declarada", max_length=16, blank=True, choices=[("inicial","Principiante"),("intermedio","Intermedio"),("avanzado","Avanzado")])
    experiencia = models.TextField("Sobre tu experiencia", max_length=1000, blank=True)
    anos = models.PositiveSmallIntegerField("Años cultivando (opcional)", null=True, blank=True, validators=[MaxValueValidator(100)])
    localidad = models.CharField("Ciudad o sector general", max_length=120, blank=True)
    visible = models.BooleanField("Mostrar mi perfil a la comunidad", default=False)

class JardinCompartido(models.Model):
    jardin = models.OneToOneField("seguimiento.Jardin", on_delete=models.CASCADE, related_name="publicacion")
    visible = models.BooleanField("Autorizo publicar este jardín y su ubicación aproximada", default=False)
    localidad = models.CharField("Ciudad o sector (sin dirección)", max_length=120)
    latitud = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitud = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    actualizada = models.DateTimeField(auto_now=True)

class Pregunta(models.Model):
    CATEGORIAS = [("cultivo","Cultivo"),("plagas","Plagas y enfermedades"),("riego","Riego"),("suelo","Suelo y nutrientes"),("experiencias","Experiencias"),("cosecha","Cosecha")]
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="preguntas_comunidad")
    titulo = models.CharField("Título de tu pregunta", max_length=180)
    contenido = models.TextField("Describe tu pregunta o experiencia", max_length=5000)
    categoria = models.CharField("Categoría", max_length=20, choices=CATEGORIAS)
    resuelta = models.BooleanField(default=False)
    oculta = models.BooleanField(default=False)
    huella = models.CharField(max_length=64, editable=False)
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-creada","-pk"]
        constraints = [models.UniqueConstraint(fields=["autor","huella"],condition=models.Q(oculta=False),name="community_unique_question")]
        indexes = [models.Index(fields=["oculta","categoria","-creada"])]

class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta,on_delete=models.CASCADE,related_name="respuestas")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="respuestas_comunidad")
    contenido = models.TextField("Tu respuesta",max_length=4000)
    huella = models.CharField(max_length=64,editable=False)
    oculta = models.BooleanField(default=False)
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["creada","pk"]
        constraints = [models.UniqueConstraint(fields=["pregunta","autor","huella"],condition=models.Q(oculta=False),name="community_unique_answer")]
