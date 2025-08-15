from django.shortcuts import render

from django.template import TemplateDoesNotExist
from django.http import JsonResponse
from django.contrib.auth import login as auth_login
from allauth.account import app_settings as allauth_settings
from allauth.account.utils import complete_signup
from allauth.account.adapter import get_adapter
from allauth.account.forms import LoginForm
from allauth.account.models import EmailAddress
from allauth.account.views import AjaxCapableProcessFormViewMixin

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from allauth.account.views import LoginView

class CustomLoginView(LoginView):
    template_name = 'account/login.html'  # ton template personnalisé

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = []
            for field, field_errors in form.errors.items():
                errors += field_errors
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        return super().form_invalid(form)

def root_page_view(request):
    form = LoginForm(request.POST or None)
    return render(request, 'pages/index-tour.html', {
        'user_authenticated': request.user.is_authenticated,
        'form': form
    })


def dynamic_pages_view(request, template_name):
    form = LoginForm(request.POST or None)
    return render(request, f'pages/{template_name}.html', {
        'user_authenticated': request.user.is_authenticated,
        'form': form
    })

class ModalLoginView(View):
    def post(self, request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': ["Connexion uniquement via le modal AJAX."]}, status=400)
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.user
            auth_login(request, user)
            # Redirection vers index-tour.html après succès
            return JsonResponse({'success': True, 'redirect_url': '/'})
        else:
            errors = []
            for field, field_errors in form.errors.items():
                errors += field_errors
            return JsonResponse({'success': False, 'errors': errors})

    def get(self, request, *args, **kwargs):
        return JsonResponse({'success': False, 'errors': ['Méthode non autorisée.']}, status=405)
