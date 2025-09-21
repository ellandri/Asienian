import random  # Added to fix NameError
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
from backoffice.models import Trip,Traveler, Booking,Review
from backoffice.forms import TripForm
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
import logging
from django.contrib import messages
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, logout
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login as auth_login
from allauth.account.views import PasswordResetView
from django.urls import reverse_lazy
from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
import logging
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from datetime import datetime

from django.http import HttpResponse  # Ajout de l'importation manquante
import json





logger = logging.getLogger(__name__)





class CustomLoginView(LoginView):
    template_name = 'pages/index-tour.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_required'] = True  # Ouvre le modal
        context['user_authenticated'] = self.request.user.is_authenticated
        context['best_trips'] = Trip.objects.filter(is_best_trip=True)
        context['form'] = LoginForm(self.request.POST or None)
        return context


def root_page_view(request):
    form = LoginForm(request.POST or None)
    best_trips = Trip.objects.filter(is_best_trip=True)
    reviews = Review.objects.filter(is_published=True, is_deleted=False)  # Fetch approved reviews
    return render(request, 'pages/index-tour.html', {
        'user_authenticated': request.user.is_authenticated,
        'form': form,
        'best_trips': best_trips,
        'login_required': request.GET.get('login_required') == 'true',
        'reviews': reviews,  # Add reviews to context,
        'rating_range': range(1, 6),  # 1 à 5 étoiles

    })


def dynamic_pages_view(request, template_name):
    allowed_pages = [
        'account-profile', 'account-travelers', 'account-payment-details','backup_data', 'dashboard', 'delete_account',
        'account-wishlist', 'account-settings', 'account-delete', 'hotel-list','index-tour',
        'sign-up', 'sign-in', 'about','contact','faq','terms-of-service','privacy-policy', 'blog-list', 'blog-single','team','help-center','help-detail',
        'blog','blog-detail','flight-list', 'tour-grid','tour-detail','blog-man-mountains','blog-attieke','blog-comoe','blog-danses', 'blog-san-pedro', 'blog-korhogo'
    ]

    if template_name not in allowed_pages:
        logger.warning(f"Tentative d'accès à un template non autorisé : {template_name}")
        raise Http404("Cette page n'existe pas.")

    form = None
    if template_name == 'sign-up':
        if request.method == 'POST':
            form = SignupForm(request.POST)
            if form.is_valid():
                user = form.save(request)
                complete_signup(request, user, allauth_settings.EMAIL_VERIFICATION, reverse('account_login'))
                messages.success(request, "Inscription réussie ! Veuillez vous connecter.")
                return redirect('account_login')
            else:
                messages.error(request, "Erreur lors de l'inscription. Veuillez vérifier les informations.")
        else:
            form = SignupForm()
    elif template_name == 'sign-in':
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                user = form.user
                auth_login(request, user)
                messages.success(request, "Connexion réussie !")
                return redirect('pages:dashboard')
            else:
                messages.error(request, "Identifiants incorrects. Veuillez réessayer.")
        else:
            form = LoginForm()

    context = {
        'user_authenticated': request.user.is_authenticated,
        'form': form,
    }
    if template_name == 'account-payment-details':
        context['bookings_with_payment'] = Booking.objects.filter(
            traveler__user=request.user,
            payment_method__isnull=False
        ).select_related('traveler', 'trip').distinct()

    try:
        return render(request, f'pages/{template_name}.html', context)
    except TemplateDoesNotExist:
        logger.error(f"Template non trouvé : pages/{template_name}.html")
        raise Http404("Template non trouvé.")

class CustomPasswordResetView(PasswordResetView):
    template_name = 'account/password_reset.html'

    def form_valid(self, form):
        form.save(
            request=self.request,
            from_email=None,
            email_template_name='account/email/password_reset_key.html',
            subject_template_name='account/email/password_reset_subject.txt',
        )
        # Redirection vers la page d'accueil (dashboard) après envoi
        return redirect('pages:dynamic_pages', template_name='index-tour')# ou 'pages:dynamic_pages', template_name='sign-in'

class ModalLoginView(View):
    def post(self, request, *args, **kwargs):
        logger.debug("Début de ModalLoginView.post")
        logger.debug(f"Données POST reçues : {request.POST}")

        # Vérifier si la requête est AJAX
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            logger.error("Requête non AJAX")
            messages.error(request, "Veuillez utiliser le formulaire de connexion via le modal.")
            return JsonResponse({
                'success': False,
                'errors': ["Requête non AJAX. Veuillez utiliser le formulaire de connexion."]
            }, status=400)

        try:
            # Initialiser le formulaire avec data et request comme arguments nommés
            form = LoginForm(data=request.POST, request=request)
            logger.debug("Formulaire créé")

            if form.is_valid():
                logger.debug("Formulaire valide")
                # Extraire les identifiants
                login_field = form.cleaned_data.get('login')
                password = form.cleaned_data.get('password')

                # Authentifier l'utilisateur
                user = authenticate(request, username=login_field, password=password)
                if user is not None:
                    # Connecter l'utilisateur
                    auth_login(request, user)
                    logger.debug(f"Connexion réussie pour l'utilisateur : {user.username}")
                    messages.success(request, "Connexion réussie !")
                    return JsonResponse({
                        'success': True,
                        'redirect_url': reverse('pages:dashboard')
                    })
                else:
                    logger.debug("Échec de l'authentification : identifiants incorrects")
                    return JsonResponse({
                        'success': False,
                        'errors': ["Identifiants incorrects. Veuillez réessayer."]
                    }, status=400)
            else:
                logger.debug(f"Formulaire invalide, erreurs : {form.errors}")
                errors = []
                for field, field_errors in form.errors.items():
                    errors.extend(field_errors)
                for error in form.non_field_errors():
                    errors.append(error)
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
        except Exception as e:
            logger.error(f"Erreur dans ModalLoginView : {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'errors': [f"Erreur serveur : {str(e)}"]
            }, status=500)

    def get(self, request, *args, **kwargs):
        logger.debug("Requête GET non autorisée pour ModalLoginView")
        return JsonResponse({
            'success': False,
            'errors': ['Méthode non autorisée.']
        }, status=405)


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




from django.shortcuts import render, get_object_or_404
from backoffice.models import Trip
from django.contrib.auth.decorators import login_required

@login_required
def tour_booking_view(request, trip_id):
    try:
        trip = get_object_or_404(Trip, id=trip_id)
    except Trip.DoesNotExist:
        logger.error(f"Voyage avec l'ID {trip_id} non trouvé.")
        return render(request, '404.html', status=404)

    # Vérifier si l'utilisateur a déjà une réservation pour ce voyage
    existing_booking = Booking.objects.filter(user=request.user, trip=trip).first()
    if existing_booking:
        logger.info(f"L'utilisateur {request.user.username} a déjà une réservation pour le voyage ID {trip_id} : Réservation ID {existing_booking.id}")
        return render(request, 'pages/tour-booking.html', {
            'trip': trip,
            'active_step': 1,
            'traveler': Traveler.objects.filter(user=request.user).first(),
            'existing_booking': existing_booking
        })

    # Vérifier si l'utilisateur a un profil Traveler
    traveler = Traveler.objects.filter(user=request.user).first()

    # Définir l'étape active et stocker traveler_id si traveler existe
    active_step = 2 if traveler else 1
    if traveler:
        request.session['traveler_id'] = traveler.id
        request.session['booking_step'] = 2
        request.session.modified = True  # Forcer l'enregistrement de la session
    else:
        request.session['booking_step'] = 1
        request.session.modified = True

    logger.info(f"L'utilisateur {request.user.username} est à l'étape {active_step} pour le voyage ID {trip_id}.")
    return render(request, 'pages/tour-booking.html', {
        'trip': trip,
        'active_step': active_step,
        'traveler': traveler,
        'existing_booking': None
    })


from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

def is_valid_visa_card(card_number):
    """Valide un numéro de carte Visa avec l'algorithme de Luhn et vérifie qu'il commence par 4."""
    if not card_number.startswith('4') or not card_number.isdigit():
        logger.warning(f"Invalid Visa card number: does not start with 4 or contains non-digits")
        return False
    # Algorithme de Luhn
    total = 0
    is_even = False
    for digit in card_number[::-1]:
        digit = int(digit)
        if is_even:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
        is_even = not is_even
    return total % 10 == 0




@login_required
@csrf_protect
def booking_process(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    user = request.user

    # Vérifier si une réservation existe déjà
    existing_booking = Booking.objects.filter(user=user, trip=trip).first()
    if existing_booking:
        logger.info(f"Utilisateur {user.username} a déjà une réservation pour le voyage ID {trip_id} : Réservation ID {existing_booking.id}")
        return JsonResponse({
            'success': False,
            'message': 'Vous avez déjà réservé ce voyage. Consultez votre profil pour plus de détails.',
            'redirect_url': reverse('pages:account_profile'),
            'booking_id': existing_booking.id
        }, status=400)

    if request.method != 'POST':
        logger.warning(f"Méthode de requête invalide : {request.method}")
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

    step = request.POST.get('step')
    logger.debug(f"Étape reçue : {step}, Données POST : {dict(request.POST)}, Fichiers : {dict(request.FILES)}, Session : {request.session.items()}")

    if step == '1':
        traveler = Traveler.objects.filter(user=user).first()
        request.session['trip_id'] = trip_id
        if traveler:
            # Si un voyageur existe, stocker traveler_id et passer à l'étape 3
            request.session['traveler_id'] = traveler.id
            request.session['booking_step'] = 3
            request.session.modified = True
            logger.debug(f"Étape 1 terminée avec voyageur existant : traveler_id={traveler.id}, booking_step=3")
            return JsonResponse({
                'success': True,
                'message': 'Étape 1 validée, passage à l\'étape 3.',
                'active_step': 3
            })
        else:
            # Pas de voyageur, passer à l'étape 2
            request.session['booking_step'] = 2
            request.session.modified = True
            logger.debug(f"Étape 1 terminée : trip_id={trip_id}, booking_step=2")
            return JsonResponse({
                'success': True,
                'message': 'Étape 1 validée, passage à l\'étape 2.',
                'active_step': 2
            })

    elif step == '2':
        # Récupérer et valider les champs du voyageur
        title = request.POST.get('title')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        date_of_birth = request.POST.get('date_of_birth')
        phone_number = request.POST.get('phone_number')
        nationality = request.POST.get('nationality')
        gender = request.POST.get('gender')
        address = request.POST.get('address')
        profile_photo = request.FILES.get('profile_photo')

        # Validation des champs requis
        required_fields = {
            'title': title,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'date_of_birth': date_of_birth,
            'gender': gender
        }
        for field_name, value in required_fields.items():
            if not value or value.strip() == '':
                logger.warning(f"Champ requis manquant : {field_name}")
                return JsonResponse({
                    'success': False,
                    'message': f"Le champ {field_name} est requis.",
                    'field': field_name
                }, status=400)

        # Validation de l'email
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            logger.warning(f"Format d'email invalide : {email}")
            return JsonResponse({
                'success': False,
                'message': "Adresse email invalide.",
                'field': 'email'
            }, status=400)

        # Validation de la date de naissance
        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            today = datetime.now().date()
            if dob >= today:
                logger.warning(f"Date de naissance invalide : {date_of_birth}")
                return JsonResponse({
                    'success': False,
                    'message': "La date de naissance doit être dans le passé.",
                    'field': 'date_of_birth'
                }, status=400)
        except ValueError:
            logger.warning(f"Format de date invalide pour date_of_birth : {date_of_birth}")
            return JsonResponse({
                'success': False,
                'message': "Format de date invalide (AAAA-MM-JJ).",
                'field': 'date_of_birth'
            }, status=400)

        # Validation du numéro de téléphone (si fourni)
        if phone_number and not re.match(r'^\+225\d{10}$', phone_number):
            logger.warning(f"Format de numéro de téléphone invalide : {phone_number}")
            return JsonResponse({
                'success': False,
                'message': "Numéro invalide (format +225xxxxxxxxxx, 10 chiffres requis).",
                'field': 'phone_number'
            }, status=400)

        # Validation de la photo de profil (si fournie)
        if profile_photo:
            if not isinstance(profile_photo, UploadedFile):
                logger.warning("Téléchargement de photo de profil invalide.")
                return JsonResponse({
                    'success': False,
                    'message': "Fichier de photo de profil invalide.",
                    'field': 'profile_photo'
                }, status=400)
            if profile_photo.size > 5 * 1024 * 1024:  # 5MB max
                logger.warning(f"Photo de profil trop volumineuse : {profile_photo.size} octets")
                return JsonResponse({
                    'success': False,
                    'message': "La photo de profil ne doit pas dépasser 5 Mo.",
                    'field': 'profile_photo'
                }, status=400)

        try:
            traveler, created = Traveler.objects.update_or_create(
                user=request.user,
                defaults={
                    'title': title,
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'date_of_birth': date_of_birth,
                    'phone_number': phone_number or None,
                    'nationality': nationality or None,
                    'gender': gender,
                    'address': address or None,
                    'profile_photo': profile_photo or None
                }
            )
            logger.debug(f"Voyageur {'créé' if created else 'mis à jour'} : ID={traveler.id}")
            request.session['traveler_id'] = traveler.id
            request.session['booking_step'] = 3
            request.session.modified = True
            return JsonResponse({
                'success': True,
                'message': 'Détails du voyageur enregistrés.',
                'active_step': 3
            })
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du voyageur : {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f"Erreur lors de l'enregistrement du voyageur : {str(e)}"
            }, status=500)

    elif step == '3':
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('reference')  # Correspond à transaction_id dans le modèle
        traveler_id = request.session.get('traveler_id')

        logger.debug(f"Données de paiement reçues : payment_method={payment_method}, transaction_id={transaction_id}, traveler_id={traveler_id}")

        if not payment_method or not transaction_id:
            logger.warning(f"Données de paiement manquantes : payment_method={payment_method}, transaction_id={transaction_id}")
            return JsonResponse({
                'success': False,
                'message': 'Méthode de paiement et référence de transaction requis.'
            }, status=400)

        # Valider le voyageur
        if not traveler_id:
            logger.error("Aucun traveler_id trouvé dans la session.")
            return JsonResponse({
                'success': False,
                'message': 'Aucun voyageur trouvé. Veuillez compléter l\'étape 2.'
            }, status=400)
        try:
            traveler = Traveler.objects.get(id=traveler_id, user=request.user)
        except Traveler.DoesNotExist:
            logger.error(f"Voyageur avec ID {traveler_id} non trouvé pour l'utilisateur {request.user.username}")
            return JsonResponse({
                'success': False,
                'message': 'Voyageur non trouvé. Veuillez compléter l\'étape 2.'
            }, status=400)

        # Valider les données de paiement selon la méthode
        payment_data = {}
        if payment_method == 'visa_card':
            card_number = request.POST.get('card_number')
            card_expiry_month = request.POST.get('card_expiry_month')
            card_expiry_year = request.POST.get('card_expiry_year')
            card_cvv = request.POST.get('card_cvv')
            cardholder_name = request.POST.get('cardholder_name')

            if not all([card_number, card_expiry_month, card_expiry_year, card_cvv, cardholder_name]):
                logger.warning("Données de carte incomplètes.")
                return JsonResponse({
                    'success': False,
                    'message': 'Tous les champs de la carte sont requis.'
                }, status=400)

            # Validation du numéro de carte (16 chiffres)
            if not re.match(r'^\d{16}$', card_number):
                logger.warning(f"Numéro de carte invalide : {card_number}")
                return JsonResponse({
                    'success': False,
                    'message': 'Numéro de carte invalide (16 chiffres requis).',
                    'field': 'card_number'
                }, status=400)

            # Validation de l'année et du mois d'expiration
            try:
                expiry_month = int(card_expiry_month)
                expiry_year = int(card_expiry_year)
                current_year = datetime.now().year % 100  # Deux derniers chiffres
                current_month = datetime.now().month
                if not (1 <= expiry_month <= 12):
                    logger.warning(f"Mois d'expiration invalide : {card_expiry_month}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Mois d\'expiration invalide (1-12).',
                        'field': 'card_expiry_month'
                    }, status=400)
                if expiry_year < current_year or (expiry_year == current_year and expiry_month < current_month):
                    logger.warning(f"Carte expirée : {card_expiry_month}/{card_expiry_year}")
                    return JsonResponse({
                        'success': False,
                        'message': 'La carte est expirée.',
                        'field': 'card_expiry_year'
                    }, status=400)
            except ValueError:
                logger.warning(f"Format de mois/année d'expiration invalide : {card_expiry_month}/{card_expiry_year}")
                return JsonResponse({
                    'success': False,
                    'message': 'Format de mois ou d\'année d\'expiration invalide.',
                    'field': 'card_expiry_month'
                }, status=400)

            # Validation du CVV
            if not re.match(r'^\d{3,4}$', card_cvv):
                logger.warning(f"CVV invalide : {card_cvv}")
                return JsonResponse({
                    'success': False,
                    'message': 'CVV invalide (3 ou 4 chiffres requis).',
                    'field': 'card_cvv'
                }, status=400)

            payment_data = {
                'card_number': card_number,
                'card_expiry_month': card_expiry_month,
                'card_expiry_year': card_expiry_year,
                'card_cvv': card_cvv,
                'cardholder_name': cardholder_name,
            }

        elif payment_method == 'mobile_money':
            mobile_money_operator = request.POST.get('mobile_money_operator')
            mobile_money_number = request.POST.get('mobile_money_number')

            if not all([mobile_money_operator, mobile_money_number]):
                logger.warning("Données de paiement mobile incomplètes.")
                return JsonResponse({
                    'success': False,
                    'message': 'Opérateur et numéro de mobile money requis.'
                }, status=400)

            # Validation du numéro de mobile money (exemple : format +225 suivi de 10 chiffres)
            if not re.match(r'^\+225\d{10}$', mobile_money_number):
                logger.warning(f"Numéro de mobile money invalide : {mobile_money_number}")
                return JsonResponse({
                    'success': False,
                    'message': 'Numéro de mobile money invalide (format +225xxxxxxxxxx).',
                    'field': 'mobile_money_number'
                }, status=400)

            payment_data = {
                'mobile_money_operator': mobile_money_operator,
                'mobile_money_number': mobile_money_number,
            }

        else:
            logger.warning(f"Méthode de paiement invalide : {payment_method}")
            return JsonResponse({
                'success': False,
                'message': 'Méthode de paiement non prise en charge.'
            }, status=400)

        # Définir le montant (par exemple, récupérer depuis le modèle Trip)
        try:
            amount = trip.price  # Suppose que le modèle Trip a un champ 'price' de type DecimalField
        except AttributeError:
            logger.error("Le modèle Trip n'a pas de champ 'price' défini.")
            return JsonResponse({
                'success': False,
                'message': 'Erreur : le prix du voyage n\'est pas défini.'
            }, status=500)

        # Créer la réservation
        try:
            booking = Booking.objects.create(
                user=user,
                trip=trip,
                traveler=traveler,
                amount=amount,
                payment_method=payment_method,
                payment_status='paid' if payment_method in ['visa_card', 'mobile_money'] else 'pending',
                transaction_id=transaction_id,
                created_at=datetime.now(),
                **payment_data  # Ajouter les champs spécifiques au paiement
            )
            logger.info(f"Réservation créée : ID={booking.id}, Utilisateur={user.username}, Voyage={trip.id}, Voyageur={traveler.id}, Montant={amount}")

            # Effacer les données de session après une réservation réussie
            request.session.pop('traveler_id', None)
            request.session.pop('trip_id', None)
            request.session.pop('booking_step', None)
            request.session.modified = True

            return JsonResponse({
                'success': True,
                'message': 'Réservation confirmée avec succès.',
                'redirect_url': reverse('pages:tour_booking'),
                'booking_id': booking.id
            })
        except Exception as e:
            logger.error(f"Erreur lors de la création de la réservation : {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f"Erreur lors de la création de la réservation : {str(e)}"
            }, status=500)

    else:
        logger.warning(f"Étape invalide reçue : {step}")
        return JsonResponse({
            'success': False,
            'message': 'Étape invalide.'
        }, status=400)

@login_required
@login_required
def tour_booking_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    traveler = Traveler.objects.filter(user=request.user).first()
    existing_booking = Booking.objects.filter(user=request.user, trip=trip).first()

    if existing_booking:
        logger.info(f"Utilisateur {request.user.username} a déjà une réservation pour le voyage ID {trip_id}")
        return render(request, 'pages/tour-booking.html', {
            'trip': trip,
            'active_step': 1,
            'traveler': traveler,
            'existing_booking': existing_booking
        })

    active_step = 2 if traveler else 1
    if traveler:
        request.session['traveler_id'] = traveler.id
        request.session['booking_step'] = 2
        request.session.modified = True
    else:
        request.session['booking_step'] = 1
        request.session.modified = True

    logger.debug(f"Utilisateur {request.user.username} à l'étape {active_step}, Session : {request.session.items()}")
    return (render(request, 'pages/tour-booking.html', {
        'trip': trip,
        'active_step': active_step,
        'traveler': traveler,
        'existing_booking': None
    }))
# @login_required
# def booking_success(request):
#     # Logique pour la page de succès de réservation
#     return render(request, 'pages/booking_success.html')



from django.utils.translation import gettext as _

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        try:
            # Désactiver le compte
            user.is_active = False
            user.save()
            # Déconnecter l'utilisateur
            logout(request)
            # Ajouter un message de succès
            messages.success(request, _("Votre compte a été désactivé avec succès."))
            # Rediriger vers la page d'accueil
            return redirect('pages:dashboard')
        except Exception as e:
            messages.error(request, _("Une erreur s'est produite lors de la désactivation de votre compte."))
            return redirect('pages:delete_account')
    return render(request, 'pages/delete_account.html')

@login_required
def backup_data_view(request):
    user = request.user
    bookings = Booking.objects.filter(user=user)
    data = [
        {
            'booking_id': booking.id,
            'traveler': f"{booking.traveler.title} {booking.traveler.first_name} {booking.traveler.last_name}",
            'departure_city': booking.trip.departure_city,
            'arrival_city': booking.trip.arrival_city,
            'departure_time': booking.trip.departure_time.strftime("%d %B %Y %H:%M"),
            'amount': float(booking.amount),
            'created_at': booking.created_at.strftime("%d %B %Y %H:%M"),
            'payment_method': booking.get_payment_method_display() or "N/A"
        }
        for booking in bookings
    ]
    response = HttpResponse(
        content_type='application/json',
        headers={'Content-Disposition': f'attachment; filename="backup_{user.username}.json"'}
    )
    json.dump(data, response, ensure_ascii=False, indent=2)
    return response
@login_required
def dashboard_view(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')[:5]
    context = {
        'bookings': [
            {
                'id': booking.id,
                'traveler': f"{booking.traveler.title} {booking.traveler.first_name} {booking.traveler.last_name}",
                'departure_city': booking.trip.departure_city,
                'arrival_city': booking.trip.arrival_city,
                'departure_time': booking.trip.departure_time.strftime("%d %B %Y %H:%M"),
                'amount': booking.amount,
                'created_at': booking.created_at.strftime("%d %B %Y %H:%M")
            }
            for booking in bookings
        ]
    }
    return render(request, 'dashboard.html', context)

# Liste de pays (simplifiée, peut être remplacée par django-countries)
COUNTRIES = [
    'Côte d\'Ivoire', 'France', 'États-Unis', 'Canada', 'Royaume-Uni', 'Allemagne',
    'Nigeria', 'Ghana', 'Maroc', 'Sénégal', 'Mali', 'Burkina Faso', 'Togo'
]

@login_required
def update_profile_view(request):
    traveler = Traveler.objects.filter(user=request.user).first()

    # Calcul du pourcentage de complétion du profil
    profile_completion = 0
    if traveler:
        fields = [
            traveler.title,
            traveler.first_name != 'Inconnu',
            traveler.last_name != 'Inconnu',
            traveler.email,
            traveler.date_of_birth,
            traveler.gender,
            traveler.phone_number,
            traveler.nationality
        ]
        filled_fields = sum(1 for field in fields if field)
        profile_completion = int((filled_fields / len(fields)) * 100)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            # Mise à jour des informations personnelles
            title = request.POST.get('title')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            date_of_birth = request.POST.get('date_of_birth')
            phone_number = request.POST.get('phone_number')
            nationality = request.POST.get('nationality')
            gender = request.POST.get('gender')
            address = request.POST.get('address')
            profile_photo = request.FILES.get('profile_photo')

            # Validation des champs requis
            required_fields = {
                'title': title,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'date_of_birth': date_of_birth,
                'gender': gender
            }
            for field_name, value in required_fields.items():
                if not value or value.strip() == '':
                    logger.warning(f"Champ requis manquant : {field_name}")
                    messages.error(request, f"Le champ {field_name} est requis.")
                    return redirect('pages:account_profile')

            # Validation du titre
            valid_titles = [choice[0] for choice in Traveler._meta.get_field('title').choices]
            if title not in valid_titles:
                logger.warning(f"Titre invalide : {title}")
                messages.error(request, "Titre invalide (choisir parmi Monsieur, Madame, Mademoiselle).")
                return redirect('pages:account_profile')

            # Validation de l'email
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                logger.warning(f"Format d'email invalide : {email}")
                messages.error(request, "Adresse email invalide.")
                return redirect('pages:account_profile')

            # Validation de la date de naissance
            try:
                dob = datetime.strptime(date_of_birth, '%d %b %Y').date()  # Format flatpickr: "d M Y"
                today = datetime.now().date()
                if dob >= today:
                    logger.warning(f"Date de naissance invalide : {date_of_birth}")
                    messages.error(request, "La date de naissance doit être dans le passé.")
                    return redirect('pages:account_profile')
            except ValueError:
                logger.warning(f"Format de date invalide pour date_of_birth : {date_of_birth}")
                messages.error(request, "Format de date invalide (ex. 25 Jan 2000).")
                return redirect('pages:account_profile')

            # Validation du numéro de téléphone (si fourni)
            if phone_number and not re.match(r'^\+225\d{8,10}$', phone_number):
                logger.warning(f"Format de numéro de téléphone invalide : {phone_number}")
                messages.error(request, "Numéro invalide (format +225xxxxxxxx, 8 à 10 chiffres).")
                return redirect('pages:account_profile')

            # Validation du genre
            valid_genders = [choice[0] for choice in Traveler.GENDER_CHOICES]
            if gender not in valid_genders:
                logger.warning(f"Genre invalide : {gender}")
                messages.error(request, "Genre invalide (choisir parmi Masculin, Féminin).")
                return redirect('pages:account_profile')

            # Validation de la nationalité
            if nationality and nationality not in COUNTRIES:
                logger.warning(f"Nationalité invalide : {nationality}")
                messages.error(request, "Nationalité non reconnue.")
                return redirect('pages:account_profile')

            # Validation de la photo de profil (si fournie)
            if profile_photo:
                if not isinstance(profile_photo, UploadedFile):
                    logger.warning("Téléchargement de photo de profil invalide.")
                    messages.error(request, "Fichier de photo de profil invalide.")
                    return redirect('pages:account_profile')
                if profile_photo.size > 5 * 1024 * 1024:  # 5MB max
                    logger.warning(f"Photo de profil trop volumineuse : {profile_photo.size} octets")
                    messages.error(request, "La photo de profil ne doit pas dépasser 5 Mo.")
                    return redirect('pages:account_profile')
                try:
                    FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])(profile_photo)
                except Exception as e:
                    logger.warning(f"Extension de fichier invalide pour la photo de profil : {str(e)}")
                    messages.error(request, "Extension de fichier invalide (jpg, jpeg, png, gif uniquement).")
                    return redirect('pages:account_profile')

            try:
                traveler, created = Traveler.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'title': title,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'date_of_birth': dob,
                        'phone_number': phone_number or None,
                        'nationality': nationality or None,
                        'gender': gender,
                        'address': address or None,
                        'profile_photo': profile_photo or None
                    }
                )
                logger.debug(f"Voyageur {'créé' if created else 'mis à jour'} : ID={traveler.id}")
                messages.success(request, 'Profil mis à jour avec succès.')
                return redirect('pages:account_profile')
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du profil : {str(e)}", exc_info=True)
                messages.error(request, f"Erreur lors de la mise à jour du profil : {str(e)}")
                return redirect('pages:account_profile')

        elif form_type == 'email':
            # Mise à jour de l'email de l'utilisateur
            new_email = request.POST.get('email')
            if not new_email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', new_email):
                logger.warning(f"Format d'email invalide : {new_email}")
                messages.error(request, "Adresse email invalide.")
                return redirect('pages:account_profile')

            try:
                request.user.email = new_email
                request.user.save()
                if traveler:
                    traveler.email = new_email
                    traveler.save()
                logger.debug(f"Email mis à jour pour l'utilisateur {request.user.username}: {new_email}")
                messages.success(request, 'Email mis à jour avec succès.')
                return redirect('pages:account_profile')
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour de l'email : {str(e)}", exc_info=True)
                messages.error(request, f"Erreur lors de la mise à jour de l'email : {str(e)}")
                return redirect('pages:account_profile')

        elif form_type == 'password':
            # Mise à jour du mot de passe
            form = PasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)  # Maintenir la session active
                logger.debug(f"Mot de passe mis à jour pour l'utilisateur {request.user.username}")
                messages.success(request, 'Mot de passe mis à jour avec succès.')
                return redirect('pages:account_profile')
            else:
                for error in form.errors.values():
                    logger.warning(f"Erreur de validation du mot de passe : {error}")
                    messages.error(request, error)
                return redirect('pages:account_profile')

        else:
            logger.warning(f"Type de formulaire invalide : {form_type}")
            messages.error(request, 'Type de formulaire invalide.')
            return redirect('pages:account_profile')

    else:
        # Requête GET : rendre la page de profil
        bookings = Booking.objects.filter(user=request.user).select_related('trip', 'traveler')
        context = {
            'traveler': traveler,
            'title_choices': Traveler._meta.get_field('title').choices,
            'gender_choices': Traveler.GENDER_CHOICES,
            'countries': COUNTRIES,
            'profile_completion': profile_completion,
            'bookings': bookings,
        }
        logger.debug(f"Rendu de la page de profil pour l'utilisateur {request.user.username}, traveler={traveler}")
        return render(request, 'pages/account-profile.html', context)

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

def add_trip_form_view(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Voyage ajouté avec succès !')
            return redirect('backoffice:admin_booking_list')
        else:
            messages.error(request, 'Erreur lors de l’ajout du voyage. Vérifiez les champs.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = TripForm()
    return render(request, 'backoffice/add-trip-form.html', {'form': form})

@csrf_exempt  # juste pour tester si le csrf pose problème




# def save_profile(request):
#     logger.debug(f"Requête POST reçue : {request.POST}")
#     if request.method == "POST":
#         try:
#             user = request.user
#             if not user.is_authenticated:
#                 logger.error("Utilisateur non authentifié")
#                 return redirect('account_login')  # Rediriger vers la page de connexion
#
#             trip_id = request.POST.get("trip_id")
#             if not trip_id:
#                 logger.error("L'ID du voyage est requis")
#                 raise ValueError("L'ID du voyage est requis")
#
#             try:
#                 trip = Trip.objects.get(id=trip_id)
#             except Trip.DoesNotExist:
#                 logger.error("Le voyage spécifié n'existe pas")
#                 raise ValueError("Le voyage spécifié n'existe pas")
#
#             # Création du traveler
#             title = request.POST.get("title")
#             first_name = request.POST.get("first_name")
#             last_name = request.POST.get("last_name")
#             date_of_birth = request.POST.get("date_of_birth")
#             email = request.POST.get("email")
#
#             if not all([title, first_name, last_name, date_of_birth, email]):
#                 logger.error("Tous les champs du traveler sont obligatoires")
#                 raise ValueError("Tous les champs du traveler sont obligatoires")
#
#             try:
#                 datetime.strptime(date_of_birth, '%Y-%m-%d')
#             except ValueError:
#                 logger.error("Format de date de naissance invalide")
#                 raise ValueError("Format de date de naissance invalide")
#
#             traveler = Traveler.objects.create(
#                 user=user,
#                 trip=trip,
#                 title=title,
#                 first_name=first_name,
#                 last_name=last_name,
#                 date_of_birth=date_of_birth,
#                 email=email,
#             )
#             logger.debug(f"Traveler créé : {traveler.id}")
#
#             # Création du booking
#             payment_method = request.POST.get("payment_method", "card")
#             card_number = request.POST.get("card_number")
#             card_expiry_month = request.POST.get("card_expiry_month")
#             card_expiry_year = request.POST.get("card_expiry_year")
#             card_cvv = request.POST.get("card_cvv")
#             cardholder_name = request.POST.get("cardholder_name")
#
#             if payment_method == "card" and not all([card_number, card_expiry_month, card_expiry_year, card_cvv, cardholder_name]):
#                 logger.error("Tous les champs de paiement sont obligatoires")
#                 raise ValueError("Tous les champs de paiement sont obligatoires")
#
#             booking = Booking.objects.create(
#                 traveler=traveler,
#                 trip=trip,
#                 status="pending",
#                 payment_method=payment_method,
#                 card_number=card_number,
#                 card_expiry_month=card_expiry_month,
#                 card_expiry_year=card_expiry_year,
#                 card_cvv=card_cvv,
#                 cardholder_name=cardholder_name,
#             )
#             logger.debug(f"Booking créé : {booking.id}")
#
#             # Redirection directe vers booking-confirm
#             return redirect('pages:booking_confirm', booking_id=booking.id)
#
#         except Exception as e:
#             logger.error(f"Erreur dans save_profile : {str(e)}")
#             # En cas d'erreur, rediriger vers une page d'erreur ou afficher un message
#             return redirect('pages:dashboard')  # Ou une page d'erreur personnalisée
#
#     logger.error("Méthode non autorisée")
#     return redirect('pages:dashboard')  # Rediriger si la méthode n'est pas POST

# def booking_confirm_view(request, booking_id):
#     booking = get_object_or_404(Booking, id=booking_id)
#     context = {
#         'booking': booking,
#         'booking_id': booking.id,
#         'trip': booking.trip,
#         'booked_by': f"{booking.traveler.title} {booking.traveler.first_name} {booking.traveler.last_name}",
#         'payment_method': booking.get_payment_method_display() or booking.payment_method or "N/A",
#         'total_price': booking.trip.price,  # Prix du voyage depuis Trip
#         'booking_date': booking.created_at.strftime('%Y-%m-%d'),  # Date de création de la réservation
#         'tour_date': booking.trip.departure_time,  # Heure de départ comme date du voyage
#     }
#     return render(request, 'pages/booking-confirm.html', context)



@login_required
def my_bookings_view(request):
    # Récupérer les réservations de l'utilisateur connecté
    bookings = Booking.objects.filter(traveler__user=request.user).select_related('trip', 'traveler')

    # Trier les réservations par payment_status
    upcoming_bookings = bookings.filter(payment_status='pending')
    canceled_bookings = bookings.filter(payment_status='canceled')
    completed_bookings = bookings.filter(payment_status='paid')

    context = {
        'user': request.user,
        'upcoming_bookings': upcoming_bookings,
        'canceled_bookings': canceled_bookings,
        'completed_bookings': completed_bookings,
    }
    return render(request, 'pages/account-bookings.html', context)

def booking_confirm_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.user != request.user:
        return render(request, 'pages/booking_confirm.html', {
            'error': _("Vous n'êtes pas autorisé à voir cette réservation.")
        })
    trip = booking.trip
    booked_by = f"{booking.traveler.title} {booking.traveler.first_name} {booking.traveler.last_name}"
    tour_date = booking.trip.departure_time.strftime("%d %B %Y %H:%M")
    payment_method = booking.get_payment_method_display() or "N/A"
    total_price = booking.amount
    booking_date = booking.created_at.strftime("%d %B %Y %H:%M")
    context = {
        'booking_id': booking.id,
        'trip': trip,
        'booked_by': booked_by,
        'tour_date': tour_date,
        'payment_method': payment_method,
        'total_price': total_price,
        'booking_date': booking_date,
    }
    return render(request, 'pages/booking-confirm.html', context)

def booking_success(request):
    return render(request, 'pages/booking_success.html', {'message': 'Votre réservation a été effectuée avec succès !'})

@login_required
def payment_details_view(request):
    # Récupérer les réservations avec des détails de paiement pour l'utilisateur connecté
    bookings_with_payment = Booking.objects.filter(
        traveler__user=request.user,
        payment_method__isnull=False
    ).select_related('traveler', 'trip').distinct()

    context = {
        'user': request.user,
        'bookings_with_payment': bookings_with_payment,
    }
    return render(request, 'pages/account-payment-details.html', context)

@login_required
def add_payment_method_view(request):
    if request.method == 'POST':
        # Extraire les données du formulaire
        card_number = request.POST.get('card_number')
        expiry_month = request.POST.get('expiry_month')
        expiry_year = request.POST.get('expiry_year')
        cvv = request.POST.get('cvv')
        cardholder_name = request.POST.get('cardholder_name')

        # Validation de base (vous pouvez l'étendre)
        if card_number and expiry_month and expiry_year and cvv and cardholder_name:
            # Exemple : Créer une nouvelle réservation ou méthode de paiement
            # Pour simplifier, nous créons une réservation fictive avec les détails de paiement
            # Idéalement, utilisez un modèle PaymentMethod dédié
            traveler = Traveler.objects.filter(user=request.user).first()
            if traveler:
                Booking.objects.create(
                    traveler=traveler,
                    trip=traveler.trip,  # Utiliser un voyage existant ou gérer de manière appropriée
                    payment_method='card',
                    card_number=card_number,
                    card_expiry_month=expiry_month,
                    card_expiry_year=expiry_year,
                    card_cvv=cvv,
                    cardholder_name=cardholder_name,
                    status='pending'
                )
                messages.success(request, 'Méthode de paiement ajoutée avec succès.')
            else:
                messages.error(request, 'Aucun profil de voyageur trouvé. Veuillez en créer un d’abord.')
        else:
            messages.error(request, 'Tous les champs sont requis.')
        return redirect('pages:payment_details')

    return redirect('pages:payment_details')

@login_required
@csrf_protect
def edit_payment_method_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, traveler__user=request.user)

    if request.method == 'POST':
        card_number = request.POST.get('card_number')
        expiry_month = request.POST.get('expiry_month')
        expiry_year = request.POST.get('expiry_year')
        cvv = request.POST.get('cvv')
        cardholder_name = request.POST.get('cardholder_name')

        if not all([card_number, expiry_month, expiry_year, cvv, cardholder_name]):
            messages.error(request, 'Tous les champs sont requis.')
            return redirect('pages:payment_details')

        # Validation du numéro de carte
        if not re.match(r'^\d{16}$', card_number.replace(' ', '')):
            messages.error(request, 'Le numéro de carte doit contenir 16 chiffres.')
            return redirect('pages:payment_details')

        # Validation de la date d'expiration
        try:
            expiry_date = datetime.strptime(f"{expiry_month}/{expiry_year}", '%m/%Y')
            if expiry_date < datetime.now():
                messages.error(request, 'La date d’expiration de la carte est passée.')
                return redirect('pages:payment_details')
        except ValueError:
            messages.error(request, 'Format de date d’expiration invalide (MM/AAAA requis).')
            return redirect('pages:payment_details')

        try:
            # Mise à jour des détails de paiement
            booking.card_number = card_number
            booking.card_expiry_month = expiry_month
            booking.card_expiry_year = expiry_year
            booking.card_cvv = cvv  # Attention : Ne stockez pas le CVV en production
            booking.cardholder_name = cardholder_name
            booking.payment_method = 'card'
            booking.save()
            messages.success(request, 'Méthode de paiement modifiée avec succès.')
        except Exception as e:
            logger.error(f"Erreur lors de la modification de la méthode de paiement pour booking {booking_id}: {str(e)}")
            messages.error(request, 'Une erreur s’est produite lors de la modification de la carte.')

        return redirect('pages:payment_details')

    return redirect('pages:payment_details')

@login_required
@csrf_protect
def delete_payment_method_view(request, payment_id):
    if request.method == 'POST':
        payment = get_object_or_404(PaymentMethod, id=payment_id, user=request.user)
        try:
            payment.delete()
            messages.success(request, 'Méthode de paiement supprimée avec succès.')
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la méthode de paiement {payment_id}: {str(e)}")
            messages.error(request, 'Une erreur s’est produite lors de la suppression de la carte.')
        return redirect('pages:payment_details')
    return redirect('pages:payment_details')

@login_required
@csrf_protect
def update_email_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            validate_email(email)
            if request.user.email == email:
                messages.error(request, "L'email saisi est identique à l'actuel.")
                return redirect('pages:account_profile')

            request.user.email = email
            request.user.save()
            messages.success(request, "Email mis à jour avec succès.")
        except ValidationError:
            messages.error(request, "Adresse email invalide.")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'email pour l'utilisateur {request.user.id}: {str(e)}")
            messages.error(request, "Une erreur s’est produite lors de la mise à jour de l'email.")
        return redirect('pages:account_profile')

    return redirect('pages:account_profile')



# Liste de pays (simplifiée, peut être remplacée par django-countries)
COUNTRIES = [
    'Côte d\'Ivoire', 'France', 'États-Unis', 'Canada', 'Royaume-Uni', 'Allemagne',
    'Nigeria', 'Ghana', 'Maroc', 'Sénégal', 'Mali', 'Burkina Faso', 'Togo'
]

@login_required
def update_profile_view(request):
    traveler = Traveler.objects.filter(user=request.user).first()

    # Calcul du pourcentage de complétion du profil
    profile_completion = 0
    if traveler:
        fields = [
            traveler.title,
            traveler.first_name != 'Inconnu',
            traveler.last_name != 'Inconnu',
            traveler.email,
            traveler.date_of_birth,
            traveler.gender,
            traveler.phone_number,
            traveler.nationality
        ]
        filled_fields = sum(1 for field in fields if field)
        profile_completion = int((filled_fields / len(fields)) * 100)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            # Mise à jour des informations personnelles
            title = request.POST.get('title')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            date_of_birth = request.POST.get('date_of_birth')
            phone_number = request.POST.get('phone_number')
            nationality = request.POST.get('nationality')
            gender = request.POST.get('gender')
            address = request.POST.get('address')
            profile_photo = request.FILES.get('profile_photo')

            # Validation des champs requis
            required_fields = {
                'title': title,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'date_of_birth': date_of_birth,
                'gender': gender
            }
            for field_name, value in required_fields.items():
                if not value or value.strip() == '':
                    logger.warning(f"Champ requis manquant : {field_name}")
                    messages.error(request, f"Le champ {field_name} est requis.")
                    return redirect('pages:account_profile')

            # Validation du titre
            valid_titles = [choice[0] for choice in Traveler._meta.get_field('title').choices]
            if title not in valid_titles:
                logger.warning(f"Titre invalide : {title}")
                messages.error(request, "Titre invalide (choisir parmi Monsieur, Madame, Mademoiselle).")
                return redirect('pages:account_profile')

            # Validation de l'email
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                logger.warning(f"Format d'email invalide : {email}")
                messages.error(request, "Adresse email invalide.")
                return redirect('pages:account_profile')

            # Validation de la date de naissance
            try:
                dob = datetime.strptime(date_of_birth, '%d %b %Y').date()  # Format flatpickr: "d M Y"
                today = datetime.now().date()
                if dob >= today:
                    logger.warning(f"Date de naissance invalide : {date_of_birth}")
                    messages.error(request, "La date de naissance doit être dans le passé.")
                    return redirect('pages:account_profile')
            except ValueError:
                logger.warning(f"Format de date invalide pour date_of_birth : {date_of_birth}")
                messages.error(request, "Format de date invalide (ex. 25 Jan 2000).")
                return redirect('pages:account_profile')

            # Validation du numéro de téléphone (si fourni)
            if phone_number and not re.match(r'^\+225\d{8,10}$', phone_number):
                logger.warning(f"Format de numéro de téléphone invalide : {phone_number}")
                messages.error(request, "Numéro invalide (format +225xxxxxxxx, 8 à 10 chiffres).")
                return redirect('pages:account_profile')

            # Validation du genre
            valid_genders = [choice[0] for choice in Traveler.GENDER_CHOICES]
            if gender not in valid_genders:
                logger.warning(f"Genre invalide : {gender}")
                messages.error(request, "Genre invalide (choisir parmi Masculin, Féminin).")
                return redirect('pages:account_profile')

            # Validation de la nationalité
            if nationality and nationality not in COUNTRIES:
                logger.warning(f"Nationalité invalide : {nationality}")
                messages.error(request, "Nationalité non reconnue.")
                return redirect('pages:account_profile')

            # Validation de la photo de profil (si fournie)
            if profile_photo:
                if not isinstance(profile_photo, UploadedFile):
                    logger.warning("Téléchargement de photo de profil invalide.")
                    messages.error(request, "Fichier de photo de profil invalide.")
                    return redirect('pages:account_profile')
                if profile_photo.size > 5 * 1024 * 1024:  # 5MB max
                    logger.warning(f"Photo de profil trop volumineuse : {profile_photo.size} octets")
                    messages.error(request, "La photo de profil ne doit pas dépasser 5 Mo.")
                    return redirect('pages:account_profile')
                try:
                    FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])(profile_photo)
                except Exception as e:
                    logger.warning(f"Extension de fichier invalide pour la photo de profil : {str(e)}")
                    messages.error(request, "Extension de fichier invalide (jpg, jpeg, png, gif uniquement).")
                    return redirect('pages:account_profile')

            try:
                traveler, created = Traveler.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'title': title,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'date_of_birth': dob,
                        'phone_number': phone_number or None,
                        'nationality': nationality or None,
                        'gender': gender,
                        'address': address or None,
                        'profile_photo': profile_photo or None
                    }
                )
                logger.debug(f"Voyageur {'créé' if created else 'mis à jour'} : ID={traveler.id}")
                messages.success(request, 'Profil mis à jour avec succès.')
                return redirect('pages:account_profile')
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du profil : {str(e)}", exc_info=True)
                messages.error(request, f"Erreur lors de la mise à jour du profil : {str(e)}")
                return redirect('pages:account_profile')

        elif form_type == 'email':
            # Mise à jour de l'email de l'utilisateur
            new_email = request.POST.get('email')
            if not new_email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', new_email):
                logger.warning(f"Format d'email invalide : {new_email}")
                messages.error(request, "Adresse email invalide.")
                return redirect('pages:account_profile')

            try:
                request.user.email = new_email
                request.user.save()
                if traveler:
                    traveler.email = new_email
                    traveler.save()
                logger.debug(f"Email mis à jour pour l'utilisateur {request.user.username}: {new_email}")
                messages.success(request, 'Email mis à jour avec succès.')
                return redirect('pages:account_profile')
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour de l'email : {str(e)}", exc_info=True)
                messages.error(request, f"Erreur lors de la mise à jour de l'email : {str(e)}")
                return redirect('pages:account_profile')

        elif form_type == 'password':
            # Mise à jour du mot de passe
            form = PasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)  # Maintenir la session active
                logger.debug(f"Mot de passe mis à jour pour l'utilisateur {request.user.username}")
                messages.success(request, 'Mot de passe mis à jour avec succès.')
                return redirect('pages:account_profile')
            else:
                for error in form.errors.values():
                    logger.warning(f"Erreur de validation du mot de passe : {error}")
                    messages.error(request, error)
                return redirect('pages:account_profile')

        else:
            logger.warning(f"Type de formulaire invalide : {form_type}")
            messages.error(request, 'Type de formulaire invalide.')
            return redirect('pages:account_profile')

    else:
        # Requête GET : rendre la page de profil
        bookings = Booking.objects.filter(user=request.user).select_related('trip', 'traveler')
        context = {
            'traveler': traveler,
            'title_choices': Traveler._meta.get_field('title').choices,
            'gender_choices': Traveler.GENDER_CHOICES,
            'countries': COUNTRIES,
            'profile_completion': profile_completion,
            'bookings': bookings,
        }
        logger.debug(f"Rendu de la page de profil pour l'utilisateur {request.user.username}, traveler={traveler}")
        return render(request, 'pages/account-profile.html', context)

def calculate_profile_completion(traveler):
    fields = [
        traveler.title,
        traveler.first_name,
        traveler.last_name,
        traveler.email,
        traveler.phone_number,
        traveler.nationality,
        traveler.date_of_birth,
        traveler.gender,
        traveler.address,
        traveler.profile_photo
    ]
    filled_fields = sum(1 for field in fields if field)
    return int((filled_fields / len(fields)) * 100)

# def update_email_view(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         try:
#             validate_email(email)
#             if request.user.email == email:
#                 messages.error(request, "L'email saisi est identique à l'actuel.")
#                 return redirect('pages:account_profile')
#
#             request.user.email = email
#             request.user.save()
#
#             # Synchroniser l'email avec Traveler
#             traveler = Traveler.objects.filter(user=request.user).first()
#             if traveler:
#                 traveler.email = email
#                 traveler.save()
#
#             messages.success(request, "Email mis à jour avec succès.")
#         except ValidationError:
#             messages.error(request, "Adresse email invalide.")
#         except Exception as e:
#             logger.error(f"Erreur lors de la mise à jour de l'email pour l'utilisateur {request.user.id}: {str(e)}")
#             messages.error(request, "Une erreur s’est produite lors de la mise à jour de l'email.")
#         return redirect('pages:account_profile')
#
#     return redirect('pages:account_profile')




@login_required
@csrf_protect
def account_travelers_view(request):
    travelers = Traveler.objects.filter(user=request.user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'add_traveler':
            # Ajout d'un nouveau voyageur
            title = request.POST.get('title')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            date_of_birth = request.POST.get('date_of_birth')
            phone_number = request.POST.get('phone_number')
            nationality = request.POST.get('nationality')
            gender = request.POST.get('gender')
            address = request.POST.get('address')
            profile_photo = request.FILES.get('profile_photo')

            # Validation des champs requis
            required_fields = {
                'title': title,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'date_of_birth': date_of_birth,
                'gender': gender
            }
            for field_name, value in required_fields.items():
                if not value or value.strip() == '':
                    logger.warning(f"Champ requis manquant : {field_name}")
                    messages.error(request, f"Le champ {field_name} est requis.")
                    return redirect('pages:account_travelers')

            # Validation du titre
            valid_titles = [choice[0] for choice in Traveler._meta.get_field('title').choices]
            if title not in valid_titles:
                logger.warning(f"Titre invalide : {title}")
                messages.error(request, "Titre invalide (choisir parmi Monsieur, Madame, Mademoiselle).")
                return redirect('pages:account_travelers')

            # Validation de l'email
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                logger.warning(f"Format d'email invalide : {email}")
                messages.error(request, "Adresse email invalide.")
                return redirect('pages:account_travelers')

            # Validation de la date de naissance
            try:
                dob = datetime.strptime(date_of_birth, '%d %b %Y').date()
                today = datetime.now().date()
                if dob >= today:
                    logger.warning(f"Date de naissance invalide : {date_of_birth}")
                    messages.error(request, "La date de naissance doit être dans le passé.")
                    return redirect('pages:account_travelers')
            except ValueError:
                logger.warning(f"Format de date invalide pour date_of_birth : {date_of_birth}")
                messages.error(request, "Format de date invalide (ex. 25 Jan 2000).")
                return redirect('pages:account_travelers')

            # Validation du numéro de téléphone (si fourni)
            if phone_number and not re.match(r'^\+225\d{8,10}$', phone_number):
                logger.warning(f"Format de numéro de téléphone invalide : {phone_number}")
                messages.error(request, "Numéro invalide (format +225xxxxxxxx, 8 à 10 chiffres).")
                return redirect('pages:account_travelers')

            # Validation du genre
            valid_genders = [choice[0] for choice in Traveler.GENDER_CHOICES]
            if gender not in valid_genders:
                logger.warning(f"Genre invalide : {gender}")
                messages.error(request, "Genre invalide (choisir parmi Masculin, Féminin).")
                return redirect('pages:account_travelers')

            # Validation de la nationalité
            if nationality and nationality not in COUNTRIES:
                logger.warning(f"Nationalité invalide : {nationality}")
                messages.error(request, "Nationalité non reconnue.")
                return redirect('pages:account_travelers')

            # Validation de la photo de profil (si fournie)
            if profile_photo:
                if not isinstance(profile_photo, UploadedFile):
                    logger.warning("Téléchargement de photo de profil invalide.")
                    messages.error(request, "Fichier de photo de profil invalide.")
                    return redirect('pages:account_travelers')
                if profile_photo.size > 5 * 1024 * 1024:  # 5MB max
                    logger.warning(f"Photo de profil trop volumineuse : {profile_photo.size} octets")
                    messages.error(request, "La photo de profil ne doit pas dépasser 5 Mo.")
                    return redirect('pages:account_travelers')
                try:
                    FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])(profile_photo)
                except Exception as e:
                    logger.warning(f"Extension de fichier invalide pour la photo de profil : {str(e)}")
                    messages.error(request, "Extension de fichier invalide (jpg, jpeg, png, gif uniquement).")
                    return redirect('pages:account_travelers')

            try:
                traveler = Traveler.objects.create(
                    user=request.user,
                    title=title,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    date_of_birth=dob,
                    phone_number=phone_number or None,
                    nationality=nationality or None,
                    gender=gender,
                    address=address or None,
                    profile_photo=profile_photo or None
                )
                logger.debug(f"Voyageur créé : ID={traveler.id}")
                messages.success(request, 'Voyageur ajouté avec succès.')
                return redirect('pages:account_travelers')
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout du voyageur : {str(e)}", exc_info=True)
                messages.error(request, f"Erreur lors de l'ajout du voyageur : {str(e)}")
                return redirect('pages:account_travelers')

        elif form_type == 'update_traveler':
            # Mise à jour d'un voyageur existant
            traveler_id = request.POST.get('traveler_id')
            try:
                traveler = Traveler.objects.get(id=traveler_id, user=request.user)
            except Traveler.DoesNotExist:
                logger.error(f"Voyageur avec ID {traveler_id} non trouvé pour l'utilisateur {request.user.username}")
                messages.error(request, "Voyageur non trouvé.")
                return redirect('pages:account_travelers')

            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            date_of_birth = request.POST.get('date_of_birth')

            # Validation des champs requis
            required_fields = {
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': date_of_birth
            }
            for field_name, value in required_fields.items():
                if not value or value.strip() == '':
                    logger.warning(f"Champ requis manquant : {field_name}")
                    messages.error(request, f"Le champ {field_name} est requis.")
                    return redirect('pages:account_travelers')

            # Validation de la date de naissance
            try:
                dob = datetime.strptime(date_of_birth, '%d %b %Y').date()
                today = datetime.now().date()
                if dob >= today:
                    logger.warning(f"Date de naissance invalide : {date_of_birth}")
                    messages.error(request, "La date de naissance doit être dans le passé.")
                    return redirect('pages:account_travelers')
            except ValueError:
                logger.warning(f"Format de date invalide pour date_of_birth : {date_of_birth}")
                messages.error(request, "Format de date invalide (ex. 25 Jan 2000).")
                return redirect('pages:account_travelers')

            try:
                traveler.first_name = first_name
                traveler.last_name = last_name
                traveler.date_of_birth = dob
                traveler.save()
                logger.debug(f"Voyageur mis à jour : ID={traveler.id}")
                messages.success(request, 'Voyageur mis à jour avec succès.')
                return redirect('pages:account_travelers')
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du voyageur : {str(e)}", exc_info=True)
                messages.error(request, f"Erreur lors de la mise à jour du voyageur : {str(e)}")
                return redirect('pages:account_travelers')

    # Requête GET : afficher la liste des voyageurs
    context = {
        'travelers': travelers,
        'title_choices': Traveler._meta.get_field('title').choices,
        'gender_choices': Traveler.GENDER_CHOICES,
        'countries': COUNTRIES,
    }
    return render(request, 'pages/account-travelers.html', context)

@login_required
@csrf_protect
def delete_traveler_view(request, traveler_id):
    if request.method == 'POST':
        try:
            traveler = Traveler.objects.get(id=traveler_id, user=request.user)
            traveler.delete()
            logger.debug(f"Voyageur supprimé : ID={traveler_id}")
            messages.success(request, 'Voyageur supprimé avec succès.')
        except Traveler.DoesNotExist:
            logger.error(f"Voyageur avec ID {traveler_id} non trouvé pour l'utilisateur {request.user.username}")
            messages.error(request, 'Voyageur non trouvé.')
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du voyageur : {str(e)}", exc_info=True)
            messages.error(request, f"Erreur lors de la suppression du voyageur : {str(e)}")
        return redirect('pages:account_travelers')
    else:
        logger.warning(f"Méthode HTTP non autorisée pour la suppression : {request.method}")
        messages.error(request, 'Méthode non autorisée.')
        return redirect('pages:account_travelers')


from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator




@login_required
def logout_view(request):
    if request.method == 'GET':
        logger.info(f"Déconnexion de l'utilisateur {request.user.username}")
        logout(request)
        messages.success(request, "Vous avez été déconnecté avec succès.")
        return redirect('pages:dashboard')
    else:
        logger.warning(f"Méthode HTTP non autorisée pour la déconnexion: {request.method}")
        return redirect('pages:account_profile')

def about_view(request):
    context = {
        'user_authenticated': request.user.is_authenticated,
    }
    return render(request, 'pages/about.html', context)

def contact_view(request):
    context = {
        'user_authenticated': request.user.is_authenticated,
    }
    return render(request, 'pages/contact.html', context)
def faqs_view(request):
    context = {
        'user_authenticated': request.user.is_authenticated,
    }
    return render(request, 'pages/faq.html', context)
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def contact(request, trip_id):
    trip = Trip.objects.get(id=trip_id)
    reviews = Review.objects.filter(trip=trip)
    return render(request, 'contact.html', {'trip': trip, 'reviews': reviews})

def submit_contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        terms = request.POST.get('terms')

        if not terms:
            messages.error(request, "Vous devez accepter les conditions générales.")
            return redirect('contact', trip_id=request.POST.get('trip_id'))

        # Logique pour traiter le formulaire de contact (par exemple, enregistrer dans une base de données ou envoyer un email)
        messages.success(request, "Votre message a été envoyé avec succès !")
        return redirect('contact', trip_id=request.POST.get('trip_id'))

    return redirect('home')  # Rediriger vers la page d'accueil si la méthode n'est pas POST

@login_required
def submit_review(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        try:
            rating = float(rating)
            if not (1 <= rating <= 5):
                messages.error(request, "La note doit être comprise entre 1 et 5.")
                return redirect('contact', trip_id=trip.id)

            Review.objects.create(
                user=request.user,
                trip=trip,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Votre avis a été soumis avec succès !")
            return redirect('contact', trip_id=trip.id)
        except ValueError:
            messages.error(request, "Veuillez entrer une note valide.")
            return redirect('contact', trip_id=trip.id)

    return redirect('contact', trip_id=trip.id)
@login_required
def contact_general(request):
    reviews = Review.objects.filter(is_published=True, is_deleted=False)
    context = {
        'reviews': reviews,
        'rating_range': range(1, 6),  # 1 à 5 étoiles
    }
    return render(request, 'pages/contact.html', context)



@login_required
def submit_general_review(request):
    if request.method == 'POST':
        comment = request.POST.get('review')
        rating = request.POST.get('rating')
        terms_accepted = request.POST.get('terms')
        name = request.POST.get('name')
        email = request.POST.get('email')
        if comment and rating and terms_accepted and name and email:
            try:
                rating = float(rating)
                if not (1 <= rating <= 5):
                    messages.error(request, "La note doit être comprise entre 1 et 5.")
                    return redirect('pages:contact_general')
                Review.objects.create(
                    user=request.user,
                    comment=comment,
                    rating=rating,
                    is_published=True,
                    is_deleted=False
                )
                messages.success(request, "Avis soumis avec succès !")
                return redirect('pages:contact_general')
            except ValueError:
                messages.error(request, "Note invalide. Veuillez entrer un nombre.")
        else:
            messages.error(request, "Veuillez remplir tous les champs et accepter les conditions.")
    reviews = Review.objects.filter(is_published=True, is_deleted=False)
    return render(request, 'pages/contact.html', {'reviews': reviews})
