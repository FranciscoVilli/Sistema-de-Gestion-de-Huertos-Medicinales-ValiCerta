from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "privacidad"
urlpatterns = [
    path(
        "privacidad/",
        TemplateView.as_view(template_name="privacidad/aviso.html"),
        name="aviso",
    ),
    path(
        "cookies/",
        TemplateView.as_view(template_name="privacidad/cookies.html"),
        name="cookies",
    ),
    path(
        "condiciones/",
        TemplateView.as_view(template_name="privacidad/condiciones.html"),
        name="condiciones",
    ),
    path("cookies/guardar/", views.guardar_cookies, name="guardar_cookies"),
    path("derechos/", views.derechos, name="derechos"),
    path("derechos/gestion/", views.gestion, name="gestion"),
    path("derechos/<uuid:pk>/", views.solicitud, name="solicitud"),
    path("derechos/<uuid:pk>/responder/", views.responder, name="responder"),
]
