from django.shortcuts import render, redirect
from django.template import TemplateDoesNotExist
from django.http import JsonResponse, Http404
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

from allauth.account.forms import SignupForm, LoginForm
from django.urls import reverse
from backoffice.models import Trip
from backoffice.forms import TripForm
from django.shortcuts import get_object_or_404



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
    best_trips = Trip.objects.filter(is_best_trip=True)
    return render(request, 'pages/index-tour.html', {
        'user_authenticated': request.user.is_authenticated,
        'form': form,
        'best_trips': best_trips,
    })



def dynamic_pages_view(request, template_name):
    if template_name == 'search_trip':
        # Empêche le rendu du template inexistant
        raise Http404("Cette page n'existe pas.")
    if template_name == 'sign-up':
        # Utiliser SignupForm pour la page d'inscription
        if request.method == 'POST':
            form = SignupForm(request.POST)
            if form.is_valid():
                form.save(request)  # Enregistre l'utilisateur
                return redirect('account_login')  # Redirige vers la page de connexion après inscription
        else:
            form = SignupForm()
    elif template_name == 'sign-in':
        # Utiliser LoginForm pour la page de connexion
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                # La connexion est gérée par django-allauth
                return redirect('home')  # Redirige vers une page après connexion réussie
        else:
            form = LoginForm()
    else:
        # Pour d'autres pages dynamiques, pas de formulaire
        form = None

    context = {
        'user_authenticated': request.user.is_authenticated,
        'form': form
    }
    if template_name == 'index-tour':
        best_trips = Trip.objects.filter(is_best_trip=True).order_by('-rating')
        context['best_trips'] = best_trips
    return render(request, f'pages/{template_name}.html', context)
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

def search_trip_view(request):
    all_trips = Trip.objects.all()
    location = request.GET.get('location', '')

    # Filtrage partiel et insensible à la casse sur la ville d'arrivée
    trips = all_trips
    if location:
        trips = trips.filter(arrival_city__icontains=location)

    # Passage au template
    return render(request, 'pages/index-tour.html', {
        'selected_location': location,
        'trips': trips,
        'user_authenticated': request.user.is_authenticated,
        'form': LoginForm(),
    })

def trip_detail_view(request, trip_id):
    from backoffice.models import Trip
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        raise Http404("Ce voyage n'existe pas.")
    # Préparation des listes pour le template
    points_forts_list = trip.points_forts.split('\n') if getattr(trip, 'points_forts', None) else []
    inclusions_list = trip.inclusions.split('\n') if getattr(trip, 'inclusions', None) else []
    exclusions_list = trip.exclusions.split('\n') if getattr(trip, 'exclusions', None) else []
    return render(request, 'pages/tour-detail.html', {
        'trip': trip,
        'points_forts_list': points_forts_list,
        'inclusions_list': inclusions_list,
        'exclusions_list': exclusions_list,
    })



def trip_edit_view(request, trip_id):
    trip = Trip.objects.get(id=trip_id)
    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            return redirect('pages:trip_detail', trip_id=trip.id)
    else:
        form = TripForm(instance=trip)
    return render(request, 'pages/tour-edit.html', {'form': form, 'trip': trip})

def tour_booking_view(request, id):
    try:
        trip = Trip.objects.get(id=id)
    except Trip.DoesNotExist:
        raise Http404("Ce voyage n'existe pas.")

    if request.method == 'POST':
        # Traiter le formulaire de réservation ici
        # Par exemple, enregistrer la réservation dans la base de données
        return redirect('pages:dashboard')  # Rediriger vers une page de confirmation ou la page d'accueil

    return render(request, 'pages/tour-booking.html', {'trip': trip})

def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)

    price_base = trip.price
    remise = (trip.price * trip.discount) / 100  # remise en FCFA
    taxes = trip.taxes
    total = price_base - remise + taxes

    context = {
        "trip": trip,
        "price_base": price_base,
        "remise": remise,
        "taxes": taxes,
        "total": total,
    }
    return render(request, "trip_detail.html", context)
