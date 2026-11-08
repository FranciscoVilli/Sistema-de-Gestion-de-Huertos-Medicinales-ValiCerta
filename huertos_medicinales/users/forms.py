from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.db import transaction
from django.forms import EmailField
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from huertos_medicinales.privacidad.models import AceptacionCondiciones
from huertos_medicinales.privacidad.preferences import VERSION

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    aceptar_condiciones = forms.BooleanField(
        label="He leído las condiciones de uso y las acepto",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["aceptar_condiciones"].help_text = format_html(
            '<a href="{}" target="_blank" rel="noopener">Condiciones de uso</a> y '
            '<a href="{}" target="_blank" rel="noopener">aviso de privacidad</a>. '
            "Los mapas externos se eligen por separado.",
            reverse("privacidad:condiciones"),
            reverse("privacidad:aviso"),
        )

    @transaction.atomic
    def save(self, request):

        user = super().save(request)
        AceptacionCondiciones.objects.create(usuario=user, version=VERSION)
        return user


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """
