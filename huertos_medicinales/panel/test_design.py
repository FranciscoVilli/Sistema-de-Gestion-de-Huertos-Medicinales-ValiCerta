from datetime import date
from html.parser import HTMLParser

import pytest
from django.urls import reverse

from huertos_medicinales.seguimiento.models import Practica

pytestmark=pytest.mark.django_db

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.main=0; self.active=[]; self.ids=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="main": self.main+=1
        if tag=="a" and attrs.get("aria-current")=="page": self.active.append(attrs.get("href"))
        if attrs.get("id"):self.ids.append(attrs["id"])

def test_shared_shell_and_crop_navigation(client,django_user_model):
    user=django_user_model.objects.create_user(email="navigation@example.invalid")
    client.force_login(user)
    crop=Practica.objects.create(participante=user,titulo="Cultivo de prueba",planta="manzanilla",inicio=date.today(),espacio="Ventana",objetivo="Observar")
    for route,args in [("workspace",[]),("seguimiento:listado",[]),("seguimiento:crear",[]),("seguimiento:detalle",[crop.pk]),("seguimiento:editar",[crop.pk]),("calendar",[]),("learning",[]),("comunidades:listado",[]),("users:detail",[user.pk]),("privacidad:cookies",[])]:
        response=client.get(reverse(route,args=args));assert response.status_code==200
        source=response.content.decode(); page=Page();page.feed(source)
        assert page.main==1
        assert len([href for href in page.active if href.startswith("/")])==1
        assert "app-ui.css" in source and "cookies-ui.css" in source
        assert "institutional-theme" not in source and "site-header" not in source
        assert "Gestión y acompañamiento" not in source
    source=client.get(reverse("seguimiento:detalle",args=[crop.pk])).content.decode()
    page=Page();page.feed(source)
    assert {"bitacora","registrar-observacion","datos-cultivo"} <= set(page.ids)
    source=client.get(reverse("seguimiento:listado")).content.decode()
    assert f'{reverse("seguimiento:detalle",args=[crop.pk])}#registrar-observacion' in source

def test_authorized_management_links_remain_accessible(client,django_user_model):
    user=django_user_model.objects.create_user(email="manager-style@example.invalid",is_staff=True,is_superuser=True)
    client.force_login(user)
    source=client.get(reverse("workspace")).content.decode()
    for route in ["seguimiento:acompanamiento","privacidad:gestion","admin:index"]:
        assert reverse(route) in source

def test_account_recovery_uses_current_login_design(client):
    for route in ["account_login","account_signup","account_reset_password"]:
        source=client.get(reverse(route)).content.decode()
        assert "garden-login.css" in source and "account-ui.css" in source
        assert "night-auth-layout" not in source and "institucional-global.css" not in source
