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
from .models import Guest







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
    valid_templates = ['login-admin', 'dashboard', 'admin-booking-detail', 'admin-trip-list']  # 'admin-booking-list' retiré

    if template_name not in valid_templates:
        raise Http404('Page non trouvée')

    # Redirection pour la page de login si l'utilisateur est authentifié
    if (request.user.is_authenticated and request.user.is_superuser and
        template_name == 'login-admin'):
        return redirect('backoffice:backoffice_dashboard')

    # Initialisation du contexte
    context = {
        'user_authenticated': request.user.is_authenticated,
    }

    # Gestion du formulaire de login
    if template_name == 'login-admin':
        form = AuthenticationForm(request, data=request.POST or None)
        if request.method == 'POST':
            if form.is_valid():
                user = form.get_user()
                if user.is_superuser:
                    login(request, user)
                    return redirect('backoffice:backoffice_dashboard')
                else:
                    error_message = 'Vous devez être un superutilisateur pour accéder au backoffice.'
                    form.add_error(None, error_message)
            else:
                error_message = 'Nom d\'utilisateur ou mot de passe incorrect.'
        context['form'] = form
        context['error_message'] = error_message if 'error_message' in locals() else None

    # Gestion de la liste des voyages
    elif template_name == 'admin-trip-list':
        trips = Trip.objects.all()  # Récupérer tous les voyages
        paginator = Paginator(trips, 10)  # 10 voyages par page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['trips'] = page_obj  # Ajouter les voyages paginés au contexte

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

    return render(request, template_path, context)

def admin_booking_list_view(request):
    trips = Trip.objects.all().order_by('-id')
    best_trips = Trip.objects.filter(is_best_trip=True).order_by('-rating')
    from django.core.paginator import Paginator
    paginator = Paginator(trips, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'trips': page_obj,
        'best_trips': best_trips,
    }
    return render(request, 'pages/admin-booking-list.html', context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def toggle_best_trip(request, trip_id):
    if request.method == 'POST':
        try:
            trip = Trip.objects.get(id=trip_id)
            trip.is_best_trip = not trip.is_best_trip
            trip.save()
            return JsonResponse({'success': True, 'is_best_trip': trip.is_best_trip})
        except Trip.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Voyage introuvable'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

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


# Vue pour les détails d'un voyage
def trip_detail_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    # Préparer le contexte pour le template dynamique
    room = {
        'name': f"Voyage de {trip.departure_city} à {trip.arrival_city}",
        'hotel_name': trip.vehicle_type,  # Type de véhicule comme nom d'hôtel
        'hotel_address': trip.departure_city,  # Ville de départ comme adresse
        'description': f"Départ: {trip.departure_city}, Arrivée: {trip.arrival_city}, Durée: {trip.duration}, Prix: {trip.price} FCFA",
        'type': trip.vehicle_type,
        'side': _('N/A'),
        'floor': _('N/A'),
        'view': _('N/A'),
        'size': _('N/A'),
        'images': [{'url': trip.image}] if trip.image else [],
    }
    context = {
        'room': room,
        'trip': trip,
        'current_booking': None,
        'bookings': [],
        'pagination': {
            'start': 0,
            'end': 0,
            'total': 0,
            'has_prev': False,
            'has_next': False,
            'pages': [],
        },
    }
    return render(request, 'pages/admin-booking-detail.html', context)

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


def admin_guest_list_view(request):
    users = User.objects.all()
    return render(request, 'pages/admin-guest-list.html', {'guests': users})


from booking.users.models import User
from .models import Trip
from django.shortcuts import get_object_or_404

def admin_agent_detail_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    # Si Trip n'est pas lié à User, on affiche tous les voyages (à adapter si relation ajoutée)
    trips = Trip.objects.all()
    return render(request, 'pages/admin-agent-detail.html', {'user': user, 'trips': trips})
