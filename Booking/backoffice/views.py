from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from booking.users.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.http import Http404
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.http import HttpResponse
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from .models import Trip
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import TripSerializer
from rest_framework import viewsets
from django.urls import reverse  # Ajoutez cet import
from .forms import TripForm
from django.core.paginator import Paginator





User = get_user_model()

class LoginAdminView(LoginView):
    template_name = "backoffice/login-admin.html"
    redirect_authenticated_user = False

    def form_valid(self, form):
        user = form.get_user()
        if user.is_superuser:
            login(self.request, user)
            return redirect('backoffice:backoffice_dashboard')  # ← Ajoutez le namespace
        else:
            form.add_error(None, "Vous devez être un superutilisateur pour accéder au backoffice.")
            return self.form_invalid(form)

class BackofficeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "backoffice/admin-dashboard.html"

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        context['message'] = _("Bienvenue dans le backoffice personnalisé !")
        return context

def dynamic_pages_view(request, template_name):
    valid_templates = ['login-admin', 'admin-booking-list', 'dashboard', 'admin-booking-detail']
    if template_name not in valid_templates:
        raise Http404('Page non trouvée')

    # Redirection seulement pour la page de login
    if (request.user.is_authenticated and request.user.is_superuser and
        template_name == 'login-admin'):
        return redirect('backoffice:backoffice_dashboard')  # ← Ajoutez le namespace

    form = None
    error_message = None
    if template_name == 'login-admin':
        form = AuthenticationForm(request, data=request.POST or None)
        if request.method == 'POST':
            if form.is_valid():
                user = form.get_user()
                if user.is_superuser:
                    login(request, user)
                    return redirect('backoffice:backoffice_dashboard')  # ← Ajoutez le namespace
                else:
                    error_message = 'Vous devez être un superutilisateur pour accéder au backoffice.'
                    form.add_error(None, error_message)
            else:
                error_message = 'Nom d\'utilisateur ou mot de passe incorrect.'

    # Déterminer le chemin du template
    try:
        if template_name == 'login-admin':
            template_path = f'backoffice/{template_name}.html'
        elif template_name == 'dashboard':
            template_path = 'backoffice/admin-dashboard.html'
        else:
            template_path = f'backoffice/{template_name}.html'
        get_template(template_path)
    except TemplateDoesNotExist:
        raise Http404('Template non trouvé')

    return render(request, template_path, {
        'user_authenticated': request.user.is_authenticated,
        'form': form,
        'error_message': error_message
    })
# class VoyageViewSet(UserPassesTestMixin, ModelViewSet):
#     queryset = Voyage.objects.all()
#     serializer_class = VoyageSerializer
#     permission_classes = [IsAdminUser]
#
#     def test_func(self):
#         return self.request.user.is_superuser

def admin_booking_list_view(request):
    # Cette logique crée une boucle infinie !
    # Si l'utilisateur est authentifié, on le redirige vers le dashboard,
    # mais cette vue EST le dashboard pour les réservations
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('backoffice:backoffice_login')  # Redirigez vers le login si non authentifié

    context = {
        'user_authenticated': request.user.is_authenticated,
        'form': None,
        'error_message': None,
        'voyages': Trip.objects.all()
    }
    return render(request, 'pages/admin-booking-list.html', context)


# class BackofficeView(APIView):
#     def get(self, request):
#         trips = Trip.objects.all()
#         serializer = TripSerializer(trips, many=True)
#         return Response(serializer.data)

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer






def add_trip_form_view(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('backoffice:admin_booking_list')  # Utilisez le nom d'URL, avec l'espace de noms
    else:
        form = TripForm()
    return render(request, 'backoffice/admin_add_trip_form.html', {'form': form})


def admin_trips_view(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('backoffice:backoffice_login')

    trips_list = Trip.objects.all()
    paginator = Paginator(trips_list, 10)  # 10 voyages par page
    page_number = request.GET.get('page')
    trips = paginator.get_page(page_number)

    return render(request, 'pages/admin-booking-list.html', {'trips': trips})


def admin_booking_list(request):
    return render(request, 'pages/admin-booking-list.html')  # Ajustez selon votre structure



# Vue pour les détails d'un voyage
def trip_detail_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)  # Remplacez Trip par Voyage si nécessaire
    return render(request, 'pages/admin-booking-detail.html', {'trip': trip})

class LogoutView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('backoffice:backoffice_login')  # ← Ajoutez le namespace


login_admin_view = LoginAdminView.as_view()
backoffice_view = BackofficeView.as_view()
logout_view = LogoutView.as_view()
dynamic_pages_view = dynamic_pages_view
admin_trips_view =admin_trips_view
trip_detail_view = trip_detail_view
add_trip_form_view = add_trip_form_view
admin_booking_list_view = admin_booking_list_view
TripViewSet = TripViewSet



