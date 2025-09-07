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
from backoffice.models import Trip,Traveler, Booking
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
    return render(request, 'pages/index-tour.html', {
        'user_authenticated': request.user.is_authenticated,
        'form': form,
        'best_trips': best_trips,
        'login_required': request.GET.get('login_required') == 'true',  # Ajouter l'indicateur
    })


def dynamic_pages_view(request, template_name):
    allowed_pages = [
        'account-profile', 'account-travelers', 'account-payment-details',
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
@csrf_exempt  # juste pour tester si le csrf pose problème


def save_profile(request):
    logger.debug(f"Requête POST reçue : {request.POST}")
    if request.method == "POST":
        try:
            user = request.user
            if not user.is_authenticated:
                logger.error("Utilisateur non authentifié")
                return redirect('account_login')  # Rediriger vers la page de connexion

            trip_id = request.POST.get("trip_id")
            if not trip_id:
                logger.error("L'ID du voyage est requis")
                raise ValueError("L'ID du voyage est requis")

            try:
                trip = Trip.objects.get(id=trip_id)
            except Trip.DoesNotExist:
                logger.error("Le voyage spécifié n'existe pas")
                raise ValueError("Le voyage spécifié n'existe pas")

            # Création du traveler
            title = request.POST.get("title")
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            date_of_birth = request.POST.get("date_of_birth")
            email = request.POST.get("email")

            if not all([title, first_name, last_name, date_of_birth, email]):
                logger.error("Tous les champs du traveler sont obligatoires")
                raise ValueError("Tous les champs du traveler sont obligatoires")

            try:
                datetime.strptime(date_of_birth, '%Y-%m-%d')
            except ValueError:
                logger.error("Format de date de naissance invalide")
                raise ValueError("Format de date de naissance invalide")

            traveler = Traveler.objects.create(
                user=user,
                trip=trip,
                title=title,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                email=email,
            )
            logger.debug(f"Traveler créé : {traveler.id}")

            # Création du booking
            payment_method = request.POST.get("payment_method", "card")
            card_number = request.POST.get("card_number")
            card_expiry_month = request.POST.get("card_expiry_month")
            card_expiry_year = request.POST.get("card_expiry_year")
            card_cvv = request.POST.get("card_cvv")
            cardholder_name = request.POST.get("cardholder_name")

            if payment_method == "card" and not all([card_number, card_expiry_month, card_expiry_year, card_cvv, cardholder_name]):
                logger.error("Tous les champs de paiement sont obligatoires")
                raise ValueError("Tous les champs de paiement sont obligatoires")

            booking = Booking.objects.create(
                traveler=traveler,
                trip=trip,
                status="pending",
                payment_method=payment_method,
                card_number=card_number,
                card_expiry_month=card_expiry_month,
                card_expiry_year=card_expiry_year,
                card_cvv=card_cvv,
                cardholder_name=cardholder_name,
            )
            logger.debug(f"Booking créé : {booking.id}")

            # Redirection directe vers booking-confirm
            return redirect('pages:booking_confirm', booking_id=booking.id)

        except Exception as e:
            logger.error(f"Erreur dans save_profile : {str(e)}")
            # En cas d'erreur, rediriger vers une page d'erreur ou afficher un message
            return redirect('pages:dashboard')  # Ou une page d'erreur personnalisée

    logger.error("Méthode non autorisée")
    return redirect('pages:dashboard')  # Rediriger si la méthode n'est pas POST

def booking_confirm_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    context = {
        'booking': booking,
        'booking_id': booking.id,
        'trip': booking.trip,
        'booked_by': f"{booking.traveler.title} {booking.traveler.first_name} {booking.traveler.last_name}",
        'payment_method': booking.get_payment_method_display() or booking.payment_method or "N/A",
        'total_price': booking.trip.price,  # Prix du voyage depuis Trip
        'booking_date': booking.created_at.strftime('%Y-%m-%d'),  # Date de création de la réservation
        'tour_date': booking.trip.departure_time,  # Heure de départ comme date du voyage
    }
    return render(request, 'pages/booking-confirm.html', context)



@login_required
def my_bookings_view(request):
    # Récupérer les réservations de l'utilisateur connecté
    bookings = Booking.objects.filter(traveler__user=request.user).select_related('trip', 'traveler')

    # Trier les réservations par statut
    upcoming_bookings = bookings.filter(status='pending')
    canceled_bookings = bookings.filter(status='canceled')
    completed_bookings = bookings.filter(status='paid')

    context = {
        'user': request.user,
        'upcoming_bookings': upcoming_bookings,
        'canceled_bookings': canceled_bookings,
        'completed_bookings': completed_bookings,
    }
    return render(request, 'pages/account-bookings.html', context)
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

@login_required
@login_required
def update_profile_view(request):
    # Récupérer ou créer le profil Traveler de l'utilisateur connecté
    traveler, created = Traveler.objects.get_or_create(
        user=request.user,
        defaults={
            'email': request.user.email or '',
            'first_name': request.user.name if hasattr(request.user, 'name') and request.user.name else 'Inconnu',
            'last_name': 'Inconnu',  # Pas de last_name dans User, donc valeur par défaut
        }
    )

    if created:
        messages.info(request, "Un nouveau profil voyageur a été créé. Veuillez le compléter.")

    # Liste statique des pays
    countries = ['CI','USA', 'France', 'India', 'UK', 'Canada', 'Germany', 'Australia']

    if request.method == 'POST':
        try:
            title = request.POST.get('title', '')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            phone_number = request.POST.get('phone_number', '')
            nationality = request.POST.get('nationality', '')
            date_of_birth = request.POST.get('date_of_birth', '')
            gender = request.POST.get('gender', '')
            address = request.POST.get('address', '')
            profile_photo = request.FILES.get('profile_photo')

            # Validations des champs obligatoires
            if not all([first_name, last_name]):
                messages.error(request, "Les champs Prénom et Nom sont obligatoires.")
                return redirect('pages:account_profile')

            # Validation de l'email (si fourni)
            if email:
                try:
                    validate_email(email)
                except ValidationError:
                    messages.error(request, "Adresse email invalide.")
                    return redirect('pages:account_profile')

            # Validation de la date de naissance (si fournie)
            parsed_date = None
            if date_of_birth:
                try:
                    parsed_date = datetime.strptime(date_of_birth, '%d %b %Y').date()
                except ValueError:
                    messages.error(request, "Format de date de naissance invalide (JJ MMM AAAA requis, ex. 29 Aug 1996).")
                    return redirect('pages:account_profile')

            # Validation de la taille de la photo de profil (si fournie)
            if profile_photo and profile_photo.size > 5 * 1024 * 1024:
                messages.error(request, "La photo de profil ne doit pas dépasser 5 Mo.")
                return redirect('pages:account_profile')

            # Validation du numéro de téléphone (si fourni)
            phone_regex = r'^\+?1?\d{9,15}$'
            if phone_number and not re.match(phone_regex, phone_number):
                messages.error(request, "Numéro de téléphone invalide (ex. +1234567890).")
                return redirect('pages:account_profile')

            # Mise à jour du profil
            traveler.title = title if title else None
            traveler.first_name = first_name
            traveler.last_name = last_name
            traveler.email = email if email else None
            traveler.phone_number = phone_number if phone_number else None
            traveler.nationality = nationality if nationality else None
            traveler.date_of_birth = parsed_date
            traveler.gender = gender if gender else None
            traveler.address = address if address else None
            if profile_photo:
                traveler.profile_photo = profile_photo
            traveler.save()

            # Synchroniser l'email avec User (si fourni)
            if email:
                request.user.email = email
                request.user.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('pages:account_profile')

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil pour l'utilisateur {request.user.id}: {str(e)}")
            messages.error(request, "Une erreur s’est produite lors de la mise à jour du profil.")
            return redirect('pages:account_profile')

    # Calculer le pourcentage de complétion du profil
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
        filled_fields = sum(1 for field in fields if field and field != 'Inconnu')
        return int((filled_fields / len(fields)) * 100)

    context = {
        'user': request.user,
        'traveler': traveler,
        'profile_completion': calculate_profile_completion(traveler),
        'countries': countries,
        'title_choices': Traveler.TITLE_CHOICES,
        'gender_choices': Traveler.GENDER_CHOICES,
    }
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
@login_required
@csrf_protect
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
def update_profile_view(request):
    # Récupérer ou créer le profil Traveler de l'utilisateur connecté
    traveler, created = Traveler.objects.get_or_create(
        user=request.user,
        defaults={
            'email': request.user.email or '',
            'first_name': request.user.name if hasattr(request.user, 'name') and request.user.name else 'Inconnu',
            'last_name': 'Inconnu',
        }
    )

    if created:
        messages.info(request, "Un nouveau profil voyageur a été créé. Veuillez le compléter.")

    # Liste statique des pays
    countries = ['USA', 'France', 'India', 'UK', 'Canada', 'Germany', 'Australia']

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            try:
                title = request.POST.get('title', '')
                first_name = request.POST.get('first_name', '')
                last_name = request.POST.get('last_name', '')
                email = request.POST.get('email', '')
                phone_number = request.POST.get('phone_number', '')
                nationality = request.POST.get('nationality', '')
                date_of_birth = request.POST.get('date_of_birth', '')
                gender = request.POST.get('gender', '')
                address = request.POST.get('address', '')
                profile_photo = request.FILES.get('profile_photo')

                # Validations des champs obligatoires
                if not all([first_name, last_name]):
                    messages.error(request, "Les champs Prénom et Nom sont obligatoires.")
                    return redirect('pages:account_profile')

                # Validation de l'email (si fourni)
                if email:
                    try:
                        validate_email(email)
                    except ValidationError:
                        messages.error(request, "Adresse email invalide.")
                        return redirect('pages:account_profile')

                # Validation de la date de naissance (si fournie)
                parsed_date = None
                if date_of_birth:
                    try:
                        parsed_date = datetime.strptime(date_of_birth, '%d %b %Y').date()
                    except ValueError:
                        messages.error(request, "Format de date de naissance invalide (JJ MMM AAAA requis, ex. 29 Aug 1996).")
                        return redirect('pages:account_profile')

                # Validation de la taille de la photo de profil (si fournie)
                if profile_photo and profile_photo.size > 5 * 1024 * 1024:
                    messages.error(request, "La photo de profil ne doit pas dépasser 5 Mo.")
                    return redirect('pages:account_profile')

                # Validation du numéro de téléphone (si fourni)
                phone_regex = r'^\+?1?\d{9,15}$'
                if phone_number and not re.match(phone_regex, phone_number):
                    messages.error(request, "Numéro de téléphone invalide (ex. +1234567890).")
                    return redirect('pages:account_profile')

                # Mise à jour du profil
                traveler.title = title if title else None
                traveler.first_name = first_name
                traveler.last_name = last_name
                traveler.email = email if email else None
                traveler.phone_number = phone_number if phone_number else None
                traveler.nationality = nationality if nationality else None
                traveler.date_of_birth = parsed_date
                traveler.gender = gender if gender else None
                traveler.address = address if address else None
                if profile_photo:
                    traveler.profile_photo = profile_photo
                traveler.save()

                # Synchroniser l'email avec User (si fourni)
                if email:
                    request.user.email = email
                    request.user.save()

                messages.success(request, "Profil mis à jour avec succès.")
                return redirect('pages:account_profile')

            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du profil pour l'utilisateur {request.user.id}: {str(e)}")
                messages.error(request, "Une erreur s’est produite lors de la mise à jour du profil.")
                return redirect('pages:account_profile')

        elif form_type == 'password':
            form = PasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)
                messages.success(request, "Mot de passe mis à jour avec succès.")
                return redirect('pages:account_profile')
            else:
                messages.error(request, "Erreur lors de la mise à jour du mot de passe. Vérifiez les champs saisis.")

        elif form_type == 'email':
            try:
                email = request.POST.get('email', '')
                if not email:
                    messages.error(request, "L'email est requis.")
                    return redirect('pages:account_profile')

                # Validation de l'email
                try:
                    validate_email(email)
                except ValidationError:
                    messages.error(request, "Adresse email invalide.")
                    return redirect('pages:account_profile')

                # Mise à jour de l'email dans User et Traveler
                request.user.email = email
                request.user.save()
                traveler.email = email
                traveler.save()

                messages.success(request, "Email mis à jour avec succès.")
                return redirect('pages:account_profile')

            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour de l'email pour l'utilisateur {request.user.id}: {str(e)}")
                messages.error(request, "Une erreur s’est produite lors de la mise à jour de l'email.")
                return redirect('pages:account_profile')

    # Calculer le pourcentage de complétion du profil
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
        filled_fields = sum(1 for field in fields if field and field != 'Inconnu')
        return int((filled_fields / len(fields)) * 100)

    context = {
        'user': request.user,
        'traveler': traveler,
        'profile_completion': calculate_profile_completion(traveler),
        'countries': countries,
        'title_choices': Traveler.TITLE_CHOICES,
        'gender_choices': Traveler.GENDER_CHOICES,
        'password_form': PasswordChangeForm(user=request.user),
    }
    return render(request, 'pages/account-profile.html', context)
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
