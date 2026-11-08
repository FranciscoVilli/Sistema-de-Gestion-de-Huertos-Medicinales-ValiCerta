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


class HuertoReal(models.Model):
    class Diseno(models.TextChoices):
        EN_TIERRA = "en_tierra", "En tierra (surcos, camadas, camellones o terrazas)"
        VERTICAL = "vertical", "Vertical (paredes)"
        COLGANTE = "colgante", "Colgante (techos)"
        PISO = "piso", "En piso (maceteros, botellas, llantas)"

    class Cerca(models.TextChoices):
        VIVA = "viva", "Cerca viva (plantas protectoras)"
        NATURAL = "natural", "Material natural (caña guadua, bahareque, tapial)"
        RECICLADO = "reciclado", "Material reciclado (tablas, botellas, neumáticos)"
        METALICA = "metalica", "Material metálico (alambre de púas)"
        CONVENCIONAL = "convencional", "Material convencional (piedra, ladrillo, bloque)"

    class Suelo(models.TextChoices):
        ARCILLOSO = "arcilloso", "Arcilloso"
        LIMOSO = "limoso", "Limoso"
        ARENOSO = "arenoso", "Arenoso"
        MARGOSO = "margoso", "Margoso"
        GREDOSO = "gredoso", "Gredoso"
        PANTANOSO = "pantanoso", "Pantanoso"

    class AguaRiego(models.TextChoices):
        RIO = "rio", "Río"
        CANAL = "canal", "Canal de riego"
        GOTEO = "goteo", "Riego por goteo"
        OTRO = "otro", "Otro"

    class Abono(models.TextChoices):
        BARBECHO = "barbecho", "Barbecho"
        RESTOS_VEGETALES = "restos_vegetales", "Restos vegetales"
        HOJA = "hoja", "Hoja"
        COMPOST = "compost", "Compost"
        OTRO = "otro", "Otro"

    class UnidadArea(models.TextChoices):
        M2 = "m2", "metros cuadrados"
        HA = "ha", "hectáreas"

    comunidad = models.OneToOneField(Comunidad, on_delete=models.CASCADE, related_name="huerto_real")
    provincia = models.CharField("Provincia", max_length=80)
    parroquia = models.CharField("Parroquia", max_length=100)
    direccion = models.CharField(
        "Dirección o referencia",
        max_length=200,
        help_text="Uso interno del establecimiento de salud; no se publica.",
    )
    latitud = models.DecimalField(
        "Latitud",
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitud = models.DecimalField(
        "Longitud",
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    tipo_diseno = models.CharField("Diseño del huerto", max_length=16, choices=Diseno)
    tecnica_diseno = models.CharField(
        "Técnica específica",
        max_length=120,
        blank=True,
        help_text="Por ejemplo: surcos, maceteros colgantes, botellas recicladas.",
    )
    tipo_cerca = models.CharField("Cerca de seguridad", max_length=16, choices=Cerca)
    detalle_cerca = models.CharField(
        "Detalle de la cerca",
        max_length=150,
        blank=True,
        help_text="Por ejemplo: higuerilla, floripondio, caña guadua.",
    )
    area_total = models.DecimalField("Área total", max_digits=8, decimal_places=2)
    unidad_area = models.CharField(max_length=4, choices=UnidadArea, default=UnidadArea.M2)
    tipo_suelo = models.CharField("Tipo de suelo", max_length=16, choices=Suelo)
    tipo_agua_riego = models.CharField("Agua de riego", max_length=16, choices=AguaRiego)
    detalle_riego = models.CharField("Detalle del riego", max_length=150, blank=True)
    tipo_abono = models.CharField("Abono natural", max_length=20, choices=Abono)
    detalle_abono = models.CharField("Detalle del abono", max_length=150, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Huerto real: {self.comunidad}"


class Bodega(models.Model):
    huerto_real = models.OneToOneField(HuertoReal, on_delete=models.CASCADE, related_name="bodega")
    tiene_espacio_herramientas = models.BooleanField("Espacio para herramientas e implementos", default=False)
    detalle_herramientas = models.CharField(max_length=150, blank=True)
    tiene_espacio_semillas = models.BooleanField(
        "Espacio para semillas, estacas, esquejes o plántulas",
        default=False,
    )
    detalle_semillas = models.CharField(max_length=150, blank=True)
    tiene_espacio_abonos = models.BooleanField("Espacio para abonos orgánicos y compost", default=False)
    detalle_abonos = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"Bodega: {self.huerto_real.comunidad}"


class Miembro(models.Model):
    class Estado(models.TextChoices):
        SOLICITADA = "solicitada", "Solicitud enviada"
        APROBADA = "aprobada", "Miembro aprobado"
        RETIRADA = "retirada", "Retirado de la comunidad"

    class Genero(models.TextChoices):
        FEMENINO = "femenino", "Femenino"
        MASCULINO = "masculino", "Masculino"
        OTRO = "otro", "Otro"
        PREFIERE_NO_DECIR = "prefiere_no_decir", "Prefiere no decir"

    class Nivel(models.TextChoices):
        APRENDIZ = "aprendiz", "Aprendiz"
        OFICIAL = "oficial", "Oficial"
        MAESTRO = "maestro", "Maestro"

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membresia")
    comunidad = models.ForeignKey(Comunidad, on_delete=models.PROTECT, related_name="miembros")
    fecha_nacimiento = models.DateField("Fecha de nacimiento")
    genero = models.CharField("Género", max_length=20, choices=Genero, blank=True)
    estado = models.CharField(max_length=16, choices=Estado, default=Estado.SOLICITADA, db_index=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["comunidad_id", "usuario_id"]

    def __str__(self):
        return f"{self.usuario}: {self.comunidad}"

    @property
    def puntos(self):
        # Se conecta a las actividades reales de cultivo en la Fase E.
        return 0

    @property
    def nivel(self):
        return self.Nivel.APRENDIZ


class CertificacionTalento(models.Model):
    class Estado(models.TextChoices):
        PROPUESTA = "propuesta", "Propuesta por la comunidad"
        CERTIFICADA = "certificada", "Certificada"
        RECHAZADA = "rechazada", "Rechazada"

    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, related_name="talentos")
    talento = models.CharField("Talento", max_length=80)
    estado = models.CharField(max_length=16, choices=Estado, default=Estado.PROPUESTA, db_index=True)
    propuesto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="talentos_propuestos",
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["miembro", "talento"],
                condition=models.Q(estado__in=["propuesta", "certificada"]),
                name="unique_active_member_talent",
            ),
        ]
        ordering = ["-creado"]
        permissions = [
            ("certificar_talento", "Certificar o rechazar talentos propuestos"),
        ]

    def __str__(self):
        return f"{self.talento}: {self.miembro}"


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
