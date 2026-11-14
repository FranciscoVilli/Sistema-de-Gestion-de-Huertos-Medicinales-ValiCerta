from django.urls import path

from .views import foto_update
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("~foto/", view=foto_update, name="foto"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
]
