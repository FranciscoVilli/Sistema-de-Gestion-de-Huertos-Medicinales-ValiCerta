from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.db import transaction

EDITORIAL = [
    ("borrador", "Borrador"),
    ("piloto", "Piloto revisable"),
    ("publicado", "Publicado"),
    ("archivado", "Archivado"),
]
VISIBLE = ("piloto", "publicado")


def validate_question(q):
    if not isinstance(q, dict) or not q.get("enunciado") or not q.get("explicacion"):
        raise ValidationError("Cada pregunta necesita enunciado y explicación.")
    options = q.get("opciones")
    if (
        not isinstance(options, list)
        or len(options) < 2
        or not all(isinstance(x, str) and x for x in options)
    ):
        raise ValidationError("Incluye al menos dos opciones de texto.")
    answer = q.get("correctas")
    if (
        not isinstance(answer, list)
        or not answer
        or any(type(i) is not int or not 0 <= i < len(options) for i in answer)
        or len(set(answer)) != len(answer)
    ):
        raise ValidationError(
            "Las respuestas correctas deben ser índices válidos y únicos.",
        )
    kind = q.get("tipo", "unica")
    if kind not in {"unica", "multiple", "booleano"}:
        raise ValidationError("Tipo de pregunta no implementado en este piloto.")
    if kind in {"unica", "booleano"} and len(answer) != 1:
        raise ValidationError("Esta pregunta requiere una sola respuesta correcta.")
    if kind == "booleano" and len(options) != 2:
        raise ValidationError("Verdadero o falso debe tener dos opciones.")


class BloqueEducativo(models.Model):
    numero = models.PositiveSmallIntegerField(unique=True)
    titulo = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["numero"]

    def __str__(self):
        return f"{self.numero}. {self.titulo}"


class CapituloEducativo(models.Model):
    bloque = models.ForeignKey(
        BloqueEducativo, on_delete=models.PROTECT, related_name="capitulos",
    )
    numero = models.PositiveSmallIntegerField(unique=True)
    slug = models.SlugField(unique=True)
    titulo = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=12, choices=EDITORIAL, default="borrador")

    class Meta:
        ordering = ["numero"]

    def __str__(self):
        return f"{self.numero}. {self.titulo}"


class FuenteEducativa(models.Model):
    titulo = models.CharField(max_length=220)
    url = models.URLField(unique=True, max_length=600)
    institucion = models.CharField(max_length=180)
    consultada = models.DateField()

    def __str__(self):
        return self.titulo


class LeccionEducativa(models.Model):
    capitulo = models.ForeignKey(
        CapituloEducativo, on_delete=models.PROTECT, related_name="lecciones",
    )
    slug = models.SlugField(unique=True)
    orden = models.PositiveSmallIntegerField()
    titulo = models.CharField(max_length=160)
    objetivos = models.TextField()
    minutos = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1)],
    )
    secciones = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de objetos con "titulo" y "texto". Texto plano.',
    )
    comprension = models.JSONField(
        default=dict,
        blank=True,
        help_text="Pregunta: enunciado, tipo (unica/multiple/booleano), opciones, correctas (índices desde 0), explicacion.",
    )
    resumen = models.TextField()
    fuentes = models.ManyToManyField(FuenteEducativa, blank=True)
    evidencia = models.CharField(
        max_length=20,
        choices=[
            ("agronomica", "Orientación agronómica contextual"),
            ("cientifica", "Conocimiento científico"),
            ("tradicional", "Conocimiento tradicional"),
            ("hipotesis", "Pendiente de validación"),
        ],
        default="agronomica",
    )
    estado = models.CharField(max_length=12, choices=EDITORIAL, default="borrador")
    revision = models.PositiveIntegerField(default=1, editable=False)
    revisada = models.DateField(null=True, blank=True)
    nota_editorial = models.TextField(blank=True)

    class Meta:
        ordering = ["capitulo__numero", "orden", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["capitulo", "orden"], name="lesson_chapter_order",
            ),
        ]

    def __str__(self):
        return self.titulo

    def clean(self):
        if self.estado in VISIBLE:
            if (
                not self.secciones
                or not isinstance(self.secciones, list)
                or any(
                    not isinstance(s, dict) or not s.get("titulo") or not s.get("texto")
                    for s in self.secciones
                )
            ):
                raise ValidationError(
                    "La lección visible necesita secciones con título y texto.",
                )
            validate_question(self.comprension)
            if not self.revisada:
                raise ValidationError("Indica la fecha de revisión documental.")

    @transaction.atomic
    def save(self, *args, **kwargs):
        previous = (
            type(self).objects.select_for_update().filter(pk=self.pk).first()
            if self.pk
            else None
        )
        # Every edit gets a new version. Existing progress stays available as history.
        if previous:
            self.revision = previous.revision + 1
        super().save(*args, **kwargs)
        RevisionEducativa.objects.create(
            leccion=self,
            numero=self.revision,
            contenido={
                "titulo": self.titulo,
                "objetivos": self.objetivos,
                "secciones": self.secciones,
                "comprension": self.comprension,
                "resumen": self.resumen,
                "estado": self.estado,
                "revisada": str(self.revisada),
                "nota_editorial": self.nota_editorial,
            },
        )


class RevisionEducativa(models.Model):
    leccion = models.ForeignKey(
        LeccionEducativa, on_delete=models.PROTECT, related_name="historial",
    )
    numero = models.PositiveIntegerField()
    contenido = models.JSONField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True,
    )
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.leccion} · rev. {self.numero}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["leccion", "numero"], name="lesson_revision_unique",
            ),
        ]


class Competencia(models.Model):
    slug = models.SlugField(unique=True)
    nombre = models.CharField(max_length=160)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre


class EvaluacionEducativa(models.Model):
    capitulo = models.OneToOneField(
        CapituloEducativo, on_delete=models.PROTECT, related_name="evaluacion",
    )
    titulo = models.CharField(max_length=160)
    preguntas = models.JSONField(
        default=list,
        blank=True,
        help_text="Banco de preguntas. Mismo formato que la comprensión de lección.",
    )
    porcentaje_minimo = models.PositiveSmallIntegerField(
        default=80, validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    competencias = models.ManyToManyField(Competencia, blank=True)
    estado = models.CharField(max_length=12, choices=EDITORIAL, default="borrador")

    def __str__(self):
        return self.titulo

    def clean(self):
        if self.estado in VISIBLE:
            if not isinstance(self.preguntas, list) or not self.preguntas:
                raise ValidationError("Incluye al menos una pregunta.")
            for q in self.preguntas:
                validate_question(q)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    porcentaje_minimo__gte=1, porcentaje_minimo__lte=100,
                ),
                name="assessment_threshold_valid",
            ),
        ]


class ProgresoLeccion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    leccion = models.ForeignKey(LeccionEducativa, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    seccion = models.PositiveIntegerField(default=0)
    completada = models.BooleanField(default=False)
    actualizada = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} · {self.leccion}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "leccion", "revision"], name="learning_progress_version",
            ),
        ]


class IntentoCapitulo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    evaluacion = models.ForeignKey(EvaluacionEducativa, on_delete=models.PROTECT)
    version = models.CharField(max_length=64)
    contenido = models.JSONField()
    respuestas = models.JSONField(default=dict)
    porcentaje = models.PositiveSmallIntegerField(null=True)
    aprobado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)
    finalizado = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.user} · {self.evaluacion}"

    class Meta:
        ordering = ["-creado"]
        indexes = [models.Index(fields=["user", "evaluacion"])]


class CompetenciaAdquirida(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    competencia = models.ForeignKey(Competencia, on_delete=models.PROTECT)
    intento = models.ForeignKey(IntentoCapitulo, on_delete=models.PROTECT)
    adquirida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} · {self.competencia}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "competencia"], name="user_competency_unique",
            ),
        ]


class RutaEducativa(models.Model):
    slug = models.SlugField(unique=True)
    nombre = models.CharField(max_length=180)
    especie = models.SlugField(
        help_text="Identificador de una especie del catálogo existente, sin duplicarla.",
    )
    descripcion = models.TextField()
    requisitos = models.ManyToManyField(Competencia, blank=True)
    lecciones = models.ManyToManyField(LeccionEducativa, blank=True)
    instrucciones = models.TextField(blank=True)
    estado = models.CharField(max_length=12, choices=EDITORIAL, default="borrador")

    def __str__(self):
        return self.nombre

    def clean(self):
        from .catalogo import PLANTAS

        if self.especie not in {p["slug"] for p in PLANTAS}:
            raise ValidationError("Selecciona un identificador de especie existente.")


class DesbloqueoRuta(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    ruta = models.ForeignKey(RutaEducativa, on_delete=models.PROTECT)
    evidencia = models.JSONField(default=dict)
    desbloqueada = models.DateTimeField(auto_now_add=True)
    iniciada = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.user} · {self.ruta}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "ruta"], name="user_route_unlock_unique",
            ),
        ]
