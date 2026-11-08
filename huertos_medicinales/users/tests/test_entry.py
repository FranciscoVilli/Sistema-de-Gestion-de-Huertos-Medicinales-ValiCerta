from http import HTTPStatus
from secrets import token_urlsafe

import pytest
from allauth.account.models import EmailAddress
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_learning_requires_login(client):
    response = client.get(reverse("learning"))
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("account_login") + "?next=/mi-aprendizaje/"


def test_verified_login_opens_learning(client, django_user_model):
    password = token_urlsafe(24)
    user = django_user_model.objects.create_user(
        email="entrada@example.com", password=password,
    )
    EmailAddress.objects.create(
        user=user, email=user.email, verified=True, primary=True,
    )
    response = client.post(
        reverse("account_login"),
        {"login": user.email, "password": password},
    )
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("workspace")
    assert client.session["_auth_user_id"] == str(user.pk)
    assert client.get(response.url).status_code == HTTPStatus.OK


def test_invalid_login_keeps_form_and_error(client):
    response = client.post(
        reverse("account_login"),
        {"login": "nadie@example.com", "password": "incorrecta"},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].non_field_errors()
    assert "_auth_user_id" not in client.session


def test_public_guide_does_not_require_account(client):
    assert client.get(reverse("first_steps")).status_code == HTTPStatus.OK


def test_home_opens_login(client):
    response = client.get(reverse("home"))
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("account_login")


def test_home_opens_workspace_for_signed_in_user(client, django_user_model):
    user = django_user_model.objects.create_user(email="home@example.com")
    client.force_login(user)
    response = client.get(reverse("home"))
    assert response.url == reverse("workspace")
