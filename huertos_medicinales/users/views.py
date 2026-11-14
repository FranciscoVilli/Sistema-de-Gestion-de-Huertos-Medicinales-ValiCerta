from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from huertos_medicinales.users.forms import FotoPerfilForm
from huertos_medicinales.users.forms import UserProfileForm
from huertos_medicinales.users.models import User

if TYPE_CHECKING:
    from django.db.models import QuerySet


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    success_message = "Tu información se guardó correctamente."

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        target=self.request.GET.get('next','')
        if target and url_has_allowed_host_and_scheme(target,allowed_hosts={self.request.get_host()},require_https=self.request.is_secure()):
            return target
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


@login_required
@require_POST
def foto_update(request):
    form = FotoPerfilForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
    else:
        messages.error(request, "No se pudo actualizar la foto. Usa una imagen válida.")
    return redirect("users:detail", pk=request.user.pk)


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


def entry(request):
    """Open the application at login, or the workspace for an active session."""
    from django.shortcuts import redirect

    return redirect("workspace" if request.user.is_authenticated else "account_login")
