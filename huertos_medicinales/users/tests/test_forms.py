"""Module for all Form Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

from huertos_medicinales.users.forms import UserAdminCreationForm
from huertos_medicinales.users.forms import UserProfileForm

if TYPE_CHECKING:
    from huertos_medicinales.users.models import User


class TestUserAdminCreationForm:
    """
    Test class for all tests related to the UserAdminCreationForm
    """

    def test_username_validation_error_msg(self, user: User):
        """
        Tests UserAdminCreation Form's unique validator functions correctly by testing:
            1) A new user with an existing username cannot be added.
            2) Only 1 error is raised by the UserCreation Form
            3) The desired error message is raised
        """

        # The user already exists,
        # hence cannot be created.
        form = UserAdminCreationForm(
            {
                "email": user.email,
                "password1": user.password,
                "password2": user.password,
            },
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors
        assert form.errors["email"][0] == _("This email has already been taken.")


class TestUserProfileForm:
    def test_no_tiene_campo_foto(self):
        assert "foto" not in UserProfileForm().fields

    def test_todos_los_campos_son_obligatorios_excepto_talentos(self):
        form = UserProfileForm()
        for campo in ["name", "fecha_nacimiento", "genero", "telefono", "direccion"]:
            assert form.fields[campo].required is True
        assert form.fields["talentos"].required is False

    def test_valido_sin_talentos(self):
        form = UserProfileForm(
            {
                "name": "Persona de Prueba",
                "fecha_nacimiento": "1990-01-01",
                "genero": "otro",
                "telefono": "0999999999",
                "direccion": "Calle Falsa 123",
                "talentos": "",
            },
        )
        assert form.is_valid()

    def test_invalido_si_falta_fecha_nacimiento(self):
        form = UserProfileForm(
            {
                "name": "Persona de Prueba",
                "fecha_nacimiento": "",
                "genero": "otro",
                "telefono": "0999999999",
                "direccion": "Calle Falsa 123",
            },
        )
        assert not form.is_valid()
        assert "fecha_nacimiento" in form.errors
