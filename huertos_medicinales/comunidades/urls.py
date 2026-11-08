from django.urls import path

from . import views, community

app_name = "comunidades"
urlpatterns = [
    path("", community.hub, name="listado"),
    path("iniciativas/", views.listado, name="iniciativas"),
    path("mapa/datos/", community.map_data, name="map_data"),
    path("preguntas/nueva/", community.question_edit, name="nueva_pregunta"),
    path("preguntas/<int:pk>/", community.question, name="pregunta"),
    path("preguntas/<int:pk>/editar/", community.question_edit, name="editar_pregunta"),
    path("preguntas/<int:pk>/estado/", community.question_action, name="estado_pregunta"),
    path("respuestas/<int:pk>/editar/", community.answer_edit, name="editar_respuesta"),
    path("perfil/editar/", community.profile_edit, name="editar_perfil"),
    path("perfil/<int:pk>/", community.profile, name="perfil"),
    path("jardines/<int:pk>/compartir/", community.share, name="compartir"),
    path("mis-solicitudes/", views.propias, name="propias"),
    path("registrar/", views.crear, name="crear"),
    path("<uuid:pk>/", views.detalle, name="detalle"),
    path("<uuid:pk>/retirar/", views.retirar, name="retirar"),
]
