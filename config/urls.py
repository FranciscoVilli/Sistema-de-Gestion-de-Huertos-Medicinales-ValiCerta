from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import RedirectView
from django.views.generic import TemplateView

from huertos_medicinales.aprendizaje import educational_views as edu
from huertos_medicinales.aprendizaje import views as learning_views
from huertos_medicinales.panel import calendar as calendar_views
from huertos_medicinales.panel import gardens
from huertos_medicinales.panel import weather
from huertos_medicinales.panel import views as panel_views
from huertos_medicinales.users.views import entry

admin.site.site_header = "Huertos Medicinales Comunitarios"
admin.site.site_title = "Gestión de Huertos"
admin.site.index_title = "Administración del sistema"

urlpatterns = [
    path("mi-aprendizaje/modulo/<int:pk>/", edu.block_detail, name="lms_block"),
    path("mi-aprendizaje/fundamentos/", edu.catalog, name="lms_catalog"),
    path("mi-aprendizaje/capitulo/<slug:slug>/", edu.chapter, name="lms_chapter"),
    path("mi-aprendizaje/contenido/<slug:slug>/", edu.lesson, name="lms_lesson"),
    path("mi-aprendizaje/evaluacion/<slug:slug>/", edu.assessment, name="lms_assessment"),
    path("mi-aprendizaje/resultado/<int:pk>/", edu.result, name="lms_result"),
    path("mi-aprendizaje/competencias/", edu.achievements, name="lms_progress"),
    path("mi-aprendizaje/ruta/<slug:slug>/", edu.route, name="lms_route"),
    path("calendario/<int:pk>/editar/", calendar_views.nueva, name="calendar_edit"),
    path("clima/localidades/", weather.places, name="weather_places"),
    path("clima/jardin/<int:pk>/", weather.garden_weather, name="garden_weather"),
    path("calendario/", calendar_views.calendario, name="calendar"),
    path("calendario/nueva/", calendar_views.nueva, name="calendar_new"),
    path("calendario/<int:pk>/completar/", calendar_views.completar, name="calendar_complete"),
    path("legal/", include("huertos_medicinales.privacidad.urls")),
    path("mi-espacio/", panel_views.inicio, name="workspace"),
    path("mi-espacio/jardines/nuevo/", gardens.nuevo, name="garden_new"),
    path("mi-espacio/jardines/<int:pk>/espacio/<int:posicion>/", gardens.colocar, name="garden_place"),
    path("mi-espacio/cultivo/<uuid:pk>/liberar/", gardens.liberar, name="garden_release"),
    path("mis-practicas/", include("huertos_medicinales.seguimiento.urls")),
    path("comunidades/", include("huertos_medicinales.comunidades.urls")),
    path("", entry, name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("huertos_medicinales.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    path(
        "vista-previa/aprendizaje/",
        learning_views.preview,
        name="learning_preview",
    ),
    path(
        "vista-previa/primera-siembra/",
        RedirectView.as_view(pattern_name="seguimiento:listado", permanent=False),
        name="challenge_preview",
    ),
    path(
        "guias/primeros-pasos/",
        TemplateView.as_view(template_name="pages/first_steps.html"),
        name="first_steps",
    ),
    path(
        "mi-aprendizaje/",
        learning_views.dashboard,
        name="learning",
    ),
    path(
        "mi-aprendizaje/leccion/<slug:slug>/",
        learning_views.lesson,
        name="learning_lesson",
    ),
    path(
        "mi-aprendizaje/planta/<slug:slug>/",
        learning_views.plant,
        name="learning_plant",
    ),
    # Your stuff: custom urls includes go here
    # ...
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]
