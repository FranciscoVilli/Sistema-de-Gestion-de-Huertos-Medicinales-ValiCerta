from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from huertos_medicinales.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from huertos_medicinales.users.models import User


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.pk}/"


@pytest.mark.django_db
def test_user_gets_a_unique_code_on_save(user: User):
    assert user.codigo_unico is not None
    assert len(user.codigo_unico) == 6
    assert user.codigo_unico.isdigit()


@pytest.mark.django_db
def test_user_code_is_not_regenerated_on_resave(user: User):
    codigo = user.codigo_unico
    user.name = "Nombre actualizado"
    user.save()
    user.refresh_from_db()
    assert user.codigo_unico == codigo


@pytest.mark.django_db
def test_user_codes_are_unique():
    uno = UserFactory.create()
    otro = UserFactory.create()
    assert uno.codigo_unico != otro.codigo_unico
