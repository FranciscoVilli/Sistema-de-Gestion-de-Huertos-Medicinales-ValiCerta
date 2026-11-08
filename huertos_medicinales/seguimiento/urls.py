from django.urls import path

from . import views

app_name = "seguimiento"
urlpatterns = [
    path("", views.listado, name="listado"),
    path("nueva/", views.crear, name="crear"),
    path("acompanamiento/", views.acompanamiento, name="acompanamiento"),
    path("<uuid:pk>/", views.detalle, name="detalle"),
    path("<uuid:pk>/editar/", views.editar, name="editar"),
    path("<uuid:pk>/estado/", views.cambiar_estado, name="estado"),
    path("<uuid:pk>/empaquetar/", views.empaquetar, name="empaquetar"),
    path("<uuid:pk>/revisar/", views.revisar, name="revisar"),
]
