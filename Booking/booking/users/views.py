from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from django.views.generic.edit import FormView
from django.contrib import messages

from booking.users.forms import UserSignupForm
from booking.users.models import User






class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None=None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


class UserSignupView(FormView):
    template_name = "pages/sign-up.html"
    form_class = UserSignupForm
    success_url = reverse_lazy("account_login")  # Redirige vers la page de connexion de django-allauth

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()  # Assure que form est toujours dans le contexte
        return context

    def form_valid(self, form):
        try:
            user = form.save(self.request)
            messages.success(self.request, _("Votre compte a été créé avec succès. Connectez-vous."))
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, _("Une erreur s'est produite : %s") % str(e))
            return self.form_invalid(form)

user_signup_view = UserSignupView.as_view()
