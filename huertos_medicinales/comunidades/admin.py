from django.contrib import admin
from django.db import transaction

from huertos_medicinales.common.admin import SoloLectura

from .models import Comunidad
from .models import EventoComunidad


@admin.register(Comunidad)
class ComunidadAdmin(SoloLectura):
    list_display = ["nombre", "provincia", "localidad", "estado", "creada"]
    list_filter = ["estado", "provincia"]
    search_fields = ["nombre", "localidad"]
    actions = ["publicar", "retirar"]

    def has_publish_permission(self, request):
        return request.user.has_perm("comunidades.publicar_comunidad")

    @admin.action(
        description="Publicar solicitudes seleccionadas",
        permissions=["publish"],
    )
    def publicar(self, request, queryset):
        with transaction.atomic():
            for comunidad in queryset.select_for_update().filter(
                estado=Comunidad.Estado.PENDIENTE,
            ):
                comunidad.estado = Comunidad.Estado.PUBLICADA
                comunidad.save(update_fields=["estado", "actualizada"])
                EventoComunidad.objects.create(
                    comunidad=comunidad,
                    actor=request.user,
                    accion="publicada",
                )
        self.message_user(request, "Solicitudes pendientes publicadas.")

    @admin.action(description="Retirar seleccionadas del mapa", permissions=["publish"])
    def retirar(self, request, queryset):
        with transaction.atomic():
            for comunidad in queryset.select_for_update().exclude(
                estado=Comunidad.Estado.RETIRADA,
            ):
                comunidad.estado = Comunidad.Estado.RETIRADA
                comunidad.save(update_fields=["estado", "actualizada"])
                EventoComunidad.objects.create(
                    comunidad=comunidad,
                    actor=request.user,
                    accion="retirada_gestion",
                )
        self.message_user(request, "Publicaciones retiradas.")


@admin.register(EventoComunidad)
class EventoComunidadAdmin(SoloLectura):
    list_display = ["comunidad", "actor", "accion", "creado"]

# Forum moderation never rewrites authorship or grants public location consent.
from .models import Pregunta, Respuesta, PerfilComunitario, JardinCompartido

class ModeracionComunitaria(SoloLectura):
    actions = ['retirar_publicaciones']
    def has_moderate_permission(self, request):
        return request.user.has_perm('comunidades.change_' + self.model._meta.model_name)
    @admin.action(description='Retirar de la comunidad', permissions=['moderate'])
    def retirar_publicaciones(self, request, queryset):
        count=queryset.update(oculta=True)
        self.message_user(request,f'{count} publicaciones retiradas.')

@admin.register(Pregunta)
class PreguntaAdmin(ModeracionComunitaria):
    list_display=['titulo','autor','categoria','resuelta','oculta','creada']
    list_filter=['oculta','resuelta','categoria']
    search_fields=['titulo','contenido']

@admin.register(Respuesta)
class RespuestaAdmin(ModeracionComunitaria):
    list_display=['pregunta','autor','oculta','creada']
    list_filter=['oculta']
    search_fields=['contenido']

@admin.register(PerfilComunitario)
class PerfilComunitarioAdmin(SoloLectura):
    list_display=['nombre','nivel','visible']
    list_filter=['visible','nivel']

@admin.register(JardinCompartido)
class JardinCompartidoAdmin(SoloLectura):
    list_display=['jardin','localidad','visible','actualizada']
    list_filter=['visible']
