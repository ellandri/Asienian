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
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import TripSerializer
from rest_framework import viewsets
from django.urls import reverse
from .forms import TripForm, TravelerForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from reportlab.pdfgen import canvas
from io import BytesIO
from django.conf import settings
from paystackapi.paystack import Paystack

from django.views.decorators.csrf import csrf_exempt
from paystackapi.transaction import Transaction
from .models import Trip, Traveler, Booking, Review


from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count

import json




User = get_user_model()

paystack = Paystack(secret_key=settings.PAYSTACK_SECRET_KEY)

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






import json
import locale

class BackofficeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "backoffice/admin-dashboard.html"

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Définir la locale française pour formater les dates
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

        # Boîtes de compteurs
        context['total_trips'] = Trip.objects.count()
        context['total_income'] = Booking.objects.filter(payment_status='paid').aggregate(total=Sum('trip__price'))['total'] or 0
        context['total_seats'] = Trip.objects.aggregate(total=Sum('available_seats'))['total'] or 0
        context['booked_seats'] = Booking.objects.filter(payment_status='paid').count()

        # Données du graphique
        today = timezone.now().date()
        last_7_days = [today - timedelta(days=x) for x in range(6, -1, -1)]
        check_ins = []
        check_outs = []
        for day in last_7_days:
            check_ins.append(Booking.objects.filter(payment_status='paid', created_at__date=day).count())
            check_outs.append(Booking.objects.filter(payment_status='paid', trip__departure_date=day).count())
        # Formater les étiquettes en français (ex. : "01 janv.")
        context['guest_traffic_labels'] = json.dumps([day.strftime('%d %b').lower() for day in last_7_days])
        context['guest_traffic_check_ins'] = json.dumps(check_ins)
        context['guest_traffic_check_outs'] = json.dumps(check_outs)
        context['check_ins'] = sum(check_ins)
        context['check_outs'] = sum(check_outs)
        context['available_seats'] = context['total_seats'] - context['booked_seats']
        context['popular_trips'] = Trip.objects.filter(is_active=True).annotate(
            booking_count=Count('bookings')
        ).order_by('-rating', '-booking_count')[:4]
        context['recent_bookings'] = Booking.objects.select_related('trip').order_by('-created_at')[:5]
        context['upcoming_arrivals'] = Booking.objects.filter(
            payment_status='paid',
            trip__departure_date__gte=today
        ).select_related('traveler', 'trip').order_by('trip__departure_date')[:6]
        context['recent_reviews'] = Review.objects.filter(
            is_published=True,
            is_deleted=False,
            trip__isnull=False
        ).select_related('trip').order_by('-created_at')[:5]

        return (context)

@csrf_exempt
@login_required
def toggle_trip_status(request, trip_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        try:
            trip = Trip.objects.get(id=trip_id)
            trip.is_active = not trip.is_active
            trip.save()
            return JsonResponse({'success': True, 'is_active': trip.is_active})
        except Trip.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Trip not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

def dynamic_pages_view(request, template_name):
    valid_templates = ['login-admin', 'dashboard', 'admin-booking-detail', 'admin-trip-list',]  # 'admin-booking-list' retiré

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



@require_POST
@login_required
def unpublish_review(request, review_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)

    review = get_object_or_404(Review, id=review_id)
    if not review.is_published:
        return JsonResponse({'success': False, 'message': 'Cet avis est déjà dépublié.'}, status=400)
    review.is_published = False
    review.save()
    return JsonResponse({'success': True, 'message': 'Avis dépublié avec succès.'})

@login_required
def backoffice_reviews(request):
    if not request.user.is_superuser:
        return redirect('backoffice:backoffice_login')

    # Filtrer par statut (all, published, deleted)
    status = request.GET.get('status', 'all')
    reviews = Review.objects.select_related('trip', 'user')
    if status == 'published':
        reviews = reviews.filter(is_published=True, is_deleted=False)
    elif status == 'deleted':
        reviews = reviews.filter(is_deleted=True)
    else:  # status == 'all'
        reviews = reviews.filter(is_deleted=False)  # Show only non-deleted reviews for "all"

    # Filtrer par voyage (trip)
    trip_id = request.GET.get('trip_id')
    if trip_id:
        reviews = reviews.filter(trip__id=trip_id)

    # Statistiques
    total_reviews = Review.objects.count()
    last_year_reviews = Review.objects.filter(
        created_at__year=timezone.now().year - 1
    ).count()
    growth_percentage = ((total_reviews - last_year_reviews) / last_year_reviews * 100) if last_year_reviews > 0 else 0

    # Pagination
    paginator = Paginator(reviews.order_by('-created_at'), 8)  # 8 avis par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Liste des voyages pour le sélecteur
    trips = Trip.objects.all()

    context = {
        'reviews': page_obj,
        'total_reviews': total_reviews,
        'growth_percentage': round(growth_percentage, 1),
        'trips': trips,
        'selected_status': status,
        'selected_trip_id': trip_id,
    }
    return render(request, 'admin-reviews.html', context)
@require_POST
@login_required
def delete_review(request, review_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)

    review = get_object_or_404(Review, id=review_id)
    review.is_deleted = True
    review.save()
    return JsonResponse({'success': True, 'message': 'Avis marqué comme supprimé.'})

@require_POST
@login_required
def publish_review(request, review_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)

    review = get_object_or_404(Review, id=review_id)
    if review.is_published:
        return JsonResponse({'success': False, 'message': 'Cet avis est déjà publié.'}, status=400)
    if review.is_deleted:
        return JsonResponse({'success': False, 'message': 'Cet avis est supprimé et ne peut pas être publié.'}, status=400)
    review.is_published = True
    review.save()
    return JsonResponse({'success': True, 'message': 'Avis publié avec succès.'})

@login_required
def direct_message(request, user_id):
    if not request.user.is_superuser:
        return redirect('backoffice:backoffice_login')

    # Retrieve the user
    user = get_object_or_404(User, id=user_id)

    # Get all reviews by this user
    reviews = Review.objects.filter(user=user, is_deleted=False).select_related('trip').order_by('-created_at')

    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            # Placeholder for sending a message (e.g., save to a Message model or send via email)
            # For now, we'll just show a success message
            messages.success(request, f"Message envoyé à {user.username} avec succès.")
            return redirect('backoffice:reviews')
        else:
            messages.error(request, "Le message ne peut pas être vide.")

    context = {
        'user': user,
        'reviews': reviews,
    }
    return render(request, 'backoffice/direct_message.html', context)
@require_POST
@login_required
def reply_to_review(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
        reply_text = request.POST.get('reply_text')
        if reply_text:
            Reply.objects.create(
                review=review,
                user=request.user,
                text=reply_text
            )
            return JsonResponse({'success': True, 'message': 'Réponse enregistrée avec succès.'})
        else:
            return JsonResponse({'success': False, 'message': 'La réponse ne peut pas être vide.'}, status=400)
    except Review.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Avis non trouvé.'}, status=404)
# def add_trip_form_view(request):
#     if request.method == 'POST':
#         form = TripForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('backoffice:admin_booking_list')  # Utilisez le nom d'URL, avec l'espace de noms
#     else:
#         form = TripForm()
#     return render(request, 'backoffice/admin_add_trip_form.html', {'form': form})

def add_trip_form_view(request):
    if request.method == 'POST':
        form = TripForm(request.POST, request.FILES)
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

# def admin_agent_detail_view(request, user_id):
#     user = get_object_or_404(User, id=user_id)
#     # Si Trip n'est pas lié à User, on affiche tous les voyages (à adapter si relation ajoutée)
#     trips = Trip.objects.all()
#     return render(request, 'pages/admin-agent-detail.html', {'user': user, 'trips': trips})




def trip_edit_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)

    if request.method == 'POST':
        print("Données POST :", request.POST)  # Débogage
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            print("Données nettoyées :", form.cleaned_data)  # Débogage
            form.save()
            messages.success(request, 'Voyage modifié avec succès !')
            return redirect('backoffice:admin-trip-detail', trip_id=trip.id)
        else:
            print("Erreurs du formulaire :", form.errors)  # Débogage
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = TripForm(instance=trip)

    return render(request, 'backoffice/admin_add_trip_form.html', {'form': form, 'trip': trip})
def traveler_create(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    success = False

    if request.method == "POST":
        form = TravelerForm(request.POST)
        if form.is_valid():
            traveler = form.save(commit=False)
            traveler.user = request.user
            traveler.trip = trip
            traveler.save()
            messages.success(request, "Profil enregistré avec succès ✅")
            success = True
            form = TravelerForm()  # réinitialiser le formulaire si besoin
    else:
        form = TravelerForm()

    return render(request, "traveler_form.html", {
        "form": form,
        "trip": trip,
        "success": success,

    })
def booking_payment(request, traveler_id, trip_id):
    if request.method == "POST" and request.is_ajax():
        try:
            traveler = get_object_or_404(Traveler, id=traveler_id)
            trip = get_object_or_404(Trip, id=trip_id)
            reference = request.POST.get("reference")  # Référence de transaction Paystack

            if not reference:
                return JsonResponse({"success": False, "message": "Aucune référence de paiement fournie"}, status=400)

            # Vérifier la transaction avec Paystack
            try:
                response = Transaction.verify(reference=reference)
                if response['status'] and response['data']['status'] == 'success':
                    paystack_payment_id = response['data']['reference']
                    # Si 3D Secure est requis, Paystack gère la redirection dans le frontend
                    booking = Booking.objects.create(
                        traveler=traveler,
                        trip=trip,
                        payment_method='visa_card',
                        paystack_payment_id=paystack_payment_id,
                        status='paid'
                    )
                    return JsonResponse({"success": True, "message": "Paiement vérifié et réservation enregistrée ✅"})
                else:
                    return JsonResponse({"success": False, "message": response['data'].get('gateway_response', 'Échec de la vérification de la carte')}, status=400)
            except Exception as e:
                return JsonResponse({"success": False, "message": f"Erreur Paystack : {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Méthode non autorisée"}, status=405)

@csrf_exempt
def booking_payment_verify(request, traveler_id, trip_id):
    try:
        traveler = get_object_or_404(Traveler, id=traveler_id)
        trip = get_object_or_404(Trip, id=trip_id)
        reference = request.GET.get("reference")

        if not reference:
            return JsonResponse({"success": False, "message": "Référence de paiement manquante"}, status=400)

        # Vérifier la transaction avec Paystack
        try:
            response = Transaction.verify(reference=reference)
            if response['status'] and response['data']['status'] == 'success':
                booking = Booking.objects.create(
                    traveler=traveler,
                    trip=trip,
                    payment_method='visa_card',
                    paystack_payment_id=response['data']['reference'],
                    status='paid'
                )
                return JsonResponse({"success": True, "message": "Paiement vérifié et réservation enregistrée ✅"})
            else:
                return JsonResponse({"success": False, "message": response['data'].get('gateway_response', 'Échec de la vérification')}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Erreur Paystack : {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# Mettre à jour admin_earnings_view (simplifié, sans références aux champs de carte)
@login_required
def admin_earnings_view(request):
    if not request.user.is_superuser:
        return redirect('backoffice:backoffice_login')

    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Utiliser payment_status au lieu de status
    daily_earnings = Booking.objects.filter(
        payment_status='paid',
        created_at__date__lte=today
    ).aggregate(avg_earnings=Avg('trip__price'))['avg_earnings'] or 0

    monthly_revenue = Booking.objects.filter(
        payment_status='paid',
        created_at__date__gte=month_start
    ).aggregate(total=Sum('trip__price'))['total'] or 0

    on_hold = Booking.objects.filter(
        payment_status='pending'
    ).aggregate(total=Sum('trip__price'))['total'] or 0

    total_balance = Booking.objects.filter(
        payment_status='paid'
    ).aggregate(total=Sum('trip__price'))['total'] or 0

    bookings_list = Booking.objects.select_related('trip', 'traveler').order_by('-created_at')
    paginator = Paginator(bookings_list, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'daily_earnings': round(daily_earnings, 2),
        'monthly_revenue': round(monthly_revenue, 2),
        'on_hold': round(on_hold, 2),
        'total_balance': round(total_balance, 2),
        'bookings': page_obj,
        # Ajouter card_number et card_expiry si nécessaire
        'card_number': bookings_list.first().card_number[-4:] if bookings_list.exists() else '****',
        'card_expiry': f"{bookings_list.first().card_expiry_month}/{bookings_list.first().card_expiry_year}" if bookings_list.exists() else 'N/A',
    }

    return render(request, 'backoffice/admin-earnings.html', context)
# Mettre à jour download_invoice pour inclure paystack_payment_id
def download_invoice(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, f"Facture #{booking.id}")
    p.drawString(100, 730, f"Date: {booking.created_at.strftime('%d %b %Y')}")
    p.drawString(100, 710, f"Voyage: {booking.trip.departure_city} à {booking.trip.arrival_city}")
    p.drawString(100, 690, f"Voyageur: {booking.traveler.first_name} {booking.traveler.last_name}")
    p.drawString(100, 670, f"Montant: {booking.trip.price} FCFA")
    p.drawString(100, 650, f"Statut: {booking.get_status_display()}")
    p.drawString(100, 630, f"ID Paiement Paystack: {booking.paystack_payment_id or 'N/A'}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf', headers={'Content-Disposition': f'attachment; filename=invoice_{booking.id}.pdf'})

# def booking_payment(request, traveler_id, trip_id):
#     if request.method == "POST" and request.is_ajax():
#         traveler = Traveler.objects.get(id=traveler_id)
#         trip = Trip.objects.get(id=trip_id)
#
#         payment_method = request.POST.get("payment_method")
#         card_number = request.POST.get("card_number")
#         card_expiry_month = request.POST.get("card_expiry_month")
#         card_expiry_year = request.POST.get("card_expiry_year")
#         card_cvv = request.POST.get("card_cvv")
#         cardholder_name = request.POST.get("cardholder_name")
#
#         booking = Booking.objects.create(
#             traveler=traveler,
#             trip=trip,
#             payment_method=payment_method,
#             card_number=card_number,
#             card_expiry_month=card_expiry_month,
#             card_expiry_year=card_expiry_year,
#             card_cvv=card_cvv,
#             cardholder_name=cardholder_name,
#             status='paid' if payment_method else 'pending'
#         )
#
#         return JsonResponse({"success": True, "message": "Paiement enregistré ✅"})
#
#     return JsonResponse({"success": False, "message": "Méthode non autorisée"}, status=405)
#
#
# @login_required
# def admin_earnings_view(request):
#     # Vérifier que l'utilisateur est superutilisateur
#     if not request.user.is_superuser:
#         return redirect('backoffice:backoffice_login')
#
#     # Calcul des métriques financières
#     today = timezone.now().date()
#     month_start = today.replace(day=1)
#
#     # Revenu quotidien moyen (moyenne des prix des voyages payés)
#     daily_earnings = Booking.objects.filter(
#         status='paid',
#         created_at__date__lte=today
#     ).aggregate(avg_earnings=Avg('trip__price'))['avg_earnings'] or 0
#
#     # Revenu ce mois-ci (somme des prix des voyages payés ce mois)
#     monthly_revenue = Booking.objects.filter(
#         status='paid',
#         created_at__date__gte=month_start
#     ).aggregate(total=Sum('trip__price'))['total'] or 0
#
#     # Montant en attente (somme des prix des voyages en attente)
#     on_hold = Booking.objects.filter(
#         status='pending'
#     ).aggregate(total=Sum('trip__price'))['total'] or 0
#
#     # Solde total (somme des prix des voyages payés)
#     total_balance = Booking.objects.filter(
#         status='paid'
#     ).aggregate(total=Sum('trip__price'))['total'] or 0
#
#     # Liste des réservations pour l'historique des paiements
#     bookings_list = Booking.objects.select_related('trip', 'traveler').order_by('-created_at')
#     paginator = Paginator(bookings_list, 8)  # 8 réservations par page
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#
#     # Contexte pour le template
#     context = {
#         'daily_earnings': round(daily_earnings, 2),
#         'monthly_revenue': round(monthly_revenue, 2),
#         'on_hold': round(on_hold, 2),
#         'total_balance': round(total_balance, 2),
#         'bookings': page_obj,
#         # Informations de la carte (prendre la dernière réservation payée avec carte)
#         'card_number': bookings_list.filter(payment_method='card').first().card_number[-4:] if bookings_list.filter(payment_method='card').exists() else '****',
#         'card_expiry': f"{bookings_list.filter(payment_method='card').first().card_expiry_month}/{bookings_list.filter(payment_method='card').first().card_expiry_year[-2:]}" if bookings_list.filter(payment_method='card').exists() else '12/26',
#     }
#
#     return render(request, 'backoffice/admin-earnings.html', context)
#
#
# def download_invoice(request, booking_id):
#     booking = get_object_or_404(Booking, id=booking_id)
#     buffer = BytesIO()
#     p = canvas.Canvas(buffer)
#     p.drawString(100, 750, f"Facture #{booking.id}")
#     p.drawString(100, 730, f"Date: {booking.created_at.strftime('%d %b %Y')}")
#     p.drawString(100, 710, f"Voyage: {booking.trip.departure_city} à {booking.trip.arrival_city}")
#     p.drawString(100, 690, f"Voyageur: {booking.traveler.first_name} {booking.traveler.last_name}")
#     p.drawString(100, 670, f"Montant: ${booking.trip.price}")
#     p.drawString(100, 650, f"Statut: {booking.get_status_display()}")
#     p.showPage()
#     p.save()
#     buffer.seek(0)
#     return HttpResponse(buffer, content_type='application/pdf', headers={'Content-Disposition': f'attachment; filename=invoice_{booking.id}.pdf'})


@csrf_exempt
def edit_card(request, booking_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)

    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)
        booking.card_number = request.POST.get('card_number')
        booking.card_expiry_month = request.POST.get('card_expiry_month')
        booking.card_expiry_year = request.POST.get('card_expiry_year')
        booking.card_cvv = request.POST.get('card_cvv')
        booking.cardholder_name = request.POST.get('cardholder_name')
        booking.save()
        return JsonResponse({
            'success': True,
            'message': 'Carte mise à jour avec succès',
            'card_number': booking.card_number[-4:],
            'card_expiry': f"{booking.card_expiry_month}/{booking.card_expiry_year[-2:]}"
        })
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)




def admin_agent_detail_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    traveler = getattr(user, "traveler", None)
    trips = Trip.objects.filter(is_active=True)
    bookings = Booking.objects.filter(user=user)

    booking_count = bookings.count()
    total_earning = sum(b.amount for b in bookings if b.payment_status == "paid")

    context = {
        "user": user,
        "traveler": traveler,
        "trips": trips,
        "bookings": bookings,
        "booking_count": booking_count,
        "total_earning": total_earning,
    }
    return render(request, "pages/admin-agent-detail.html", context)


@login_required
def admin_reviews_view(request):
    if not request.user.is_superuser:
        return redirect('backoffice:backoffice_login')

    # Filtrer par statut (all, published, deleted)
    status = request.GET.get('status', 'all')
    reviews = Review.objects.select_related('trip', 'traveler')
    if status == 'published':
        reviews = reviews.filter(status='published')
    elif status == 'deleted':
        reviews = reviews.filter(status='deleted')

    # Filtrer par voyage (trip)
    trip_id = request.GET.get('trip_id')
    if trip_id:
        reviews = reviews.filter(trip__id=trip_id)

    # Statistiques
    total_reviews = Review.objects.count()
    last_year_reviews = Review.objects.filter(
        created_at__year=timezone.now().year - 1
    ).count()
    growth_percentage = ((total_reviews - last_year_reviews) / last_year_reviews * 100) if last_year_reviews > 0 else 0

    # Pagination
    paginator = Paginator(reviews.order_by('-created_at'), 8)  # 8 avis par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Liste des voyages pour le sélecteur
    trips = Trip.objects.all()

    context = {
        'reviews': page_obj,
        'total_reviews': total_reviews,
        'growth_percentage': round(growth_percentage, 1),
        'trips': trips,
        'selected_status': status,
        'selected_trip_id': trip_id,
    }
    return render(request, 'backoffice/admin-reviews.html', context)

@csrf_exempt
def reply_to_review(request, review_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)

    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        reply_text = request.POST.get('reply_text')
        if reply_text:
            review.comment += f"\n\nRéponse de l'admin: {reply_text}"
            review.save()
            return JsonResponse({'success': True, 'message': 'Réponse enregistrée'})
        return JsonResponse({'success': False, 'message': 'Réponse vide'}, status=400)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

@csrf_exempt
def delete_review(request, review_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)

    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        review.status = 'deleted'
        review.save()
        return JsonResponse({'success': True, 'message': 'Avis marqué comme supprimé'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from paystackapi.paystack import Paystack
from paystackapi.transaction import Transaction
from django.conf import settings
from .models import Trip, Traveler, Booking, Review
from .forms import TripForm, TravelerForm
from django.contrib import messages
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import Traveler


# Configurer Paystack
paystack = Paystack(secret_key=settings.PAYSTACK_SECRET_KEY)

@login_required
# Fonction pour valider le numéro de carte Visa avec l'algorithme Luhn
def is_valid_visa_card(card_number):
    """Validation du numéro de carte Visa avec l'algorithme Luhn"""
    if not card_number or len(card_number.replace(' ', '')) != 16 or not card_number.startswith('4'):
        return False
    digits = [int(d) for d in card_number.replace(' ', '')]
    checksum = 0
    is_even = False
    for digit in digits[::-1]:
        if is_even:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
        is_even = not is_even
    return checksum % 10 == 0

@login_required
def booking_process(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    user = request.user

    if request.method == 'POST':
        step = request.POST.get('step')

        if step == '2':
            # Enregistrer les informations du voyageur (Step 2)
            title = request.POST.get('title')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            date_of_birth = request.POST.get('date_of_birth')
            phone_number = request.POST.get('phone_number')
            nationality = request.POST.get('nationality')
            gender = request.POST.get('gender')
            address = request.POST.get('address')

            if not all([title, first_name, last_name, email, date_of_birth]):
                messages.error(request, "Les champs obligatoires (*) doivent être remplis.")
                return render(request, 'pages/booking.html', {
                    'trip': trip,
                    'user': user,
                    'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
                    'timestamp': int(timezone.now().timestamp()),
                    'active_step': 2,
                    'Traveler': Traveler,
                })

            try:
                # Validation de la date de naissance
                date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                if date_of_birth > timezone.now().date():
                    messages.error(request, "La date de naissance ne peut pas être dans le futur.")
                    return render(request, 'pages/booking.html', {
                        'trip': trip,
                        'user': user,
                        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
                        'timestamp': int(timezone.now().timestamp()),
                        'active_step': 2,
                        'Traveler': Traveler,
                    })
            except ValueError:
                messages.error(request, "Format de date de naissance invalide (utilisez AAAA-MM-JJ).")
                return render(request, 'pages/booking.html', {
                    'trip': trip,
                    'user': user,
                    'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
                    'timestamp': int(timezone.now().timestamp()),
                    'active_step': 2,
                    'Traveler': Traveler,
                })

            traveler_data = {
                'title': title,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'date_of_birth': date_of_birth,
                'phone_number': phone_number,
                'nationality': nationality,
                'gender': gender,
                'address': address,
            }
            traveler, created = Traveler.objects.update_or_create(
                user=user,
                defaults=traveler_data
            )

            if 'profile_photo' in request.FILES:
                traveler.profile_photo = request.FILES['profile_photo']
                traveler.save()

            request.session['traveler_id'] = traveler.id
            request.session['trip_id'] = trip.id

            return render(request, 'pages/booking.html', {
                'trip': trip,
                'user': user,
                'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
                'timestamp': int(timezone.now().timestamp()),
                'active_step': 3,
                'Traveler': Traveler,
            })

        elif step == '3':
            payment_method = request.POST.get('payment_method')
            traveler_id = request.session.get('traveler_id')
            trip_id = request.session.get('trip_id')

            if not traveler_id or not trip_id:
                return JsonResponse({'success': False, 'message': 'Session invalide. Veuillez recommencer.'}, status=400)

            traveler = get_object_or_404(Traveler, id=traveler_id)
            trip = get_object_or_404(Trip, id=trip_id)

            if payment_method == 'visa_card':
                card_number = request.POST.get('card_number', '').replace(' ', '')
                card_expiry_month = request.POST.get('card_expiry_month')
                card_expiry_year = request.POST.get('card_expiry_year')
                card_cvv = request.POST.get('card_cvv')
                cardholder_name = request.POST.get('cardholder_name')

                # Validation simulation
                if not all([card_number, card_expiry_month, card_expiry_year, card_cvv, cardholder_name]):
                    return JsonResponse({'success': False, 'message': 'Tous les champs de la carte sont requis'}, status=400)

                if len(card_number) != 16 or not is_valid_visa_card(card_number):
                    return JsonResponse({'success': False, 'message': 'Numéro de carte Visa invalide (doit commencer par 4 et être valide Luhn)'}, status=400)

                if len(card_cvv) != 3 or not card_cvv.isdigit():
                    return JsonResponse({'success': False, 'message': 'CVV doit être 3 chiffres'}, status=400)

                try:
                    expiry_date = datetime(int(card_expiry_year), int(card_expiry_month), 1)
                    if expiry_date < timezone.now():
                        return JsonResponse({'success': False, 'message': "Date d'expiration passée"}, status=400)
                except ValueError:
                    return JsonResponse({'success': False, 'message': 'Date d\'expiration invalide'}, status=400)

                # Simulation réussie
                booking = Booking.objects.create(
                    traveler=traveler,
                    trip=trip,
                    payment_method='visa_card',
                    reference=f'simulated-visa-{int(timezone.now().timestamp())}',
                    card_number=card_number[-4:],  # Masquer sauf 4 derniers chiffres
                    card_expiry_month=card_expiry_month,
                    card_expiry_year=card_expiry_year,
                    card_cvv='***',  # Ne pas stocker le CVV réel
                    cardholder_name=cardholder_name,
                    status='paid'
                )
                del request.session['traveler_id']
                del request.session['trip_id']
                messages.success(request, 'Paiement Visa simulé avec succès ! Réservation confirmée.')
                return JsonResponse({
                    'success': True,
                    'message': 'Paiement Visa simulé avec succès ! Réservation confirmée.',
                    'redirect_url': reverse('pages:booking_success')
                })

            elif payment_method == 'mobile_money':
                mobile_money_operator = request.POST.get('mobile_money_operator')
                mobile_money_number = request.POST.get('mobile_money_number')
                otp_entered = request.POST.get('otp_code')

                if not all([mobile_money_operator, mobile_money_number]):
                    return JsonResponse({'success': False, 'message': 'Opérateur et numéro Mobile Money requis'}, status=400)

                if not re.match(r'^\+225\d{8,10}$', mobile_money_number):
                    return JsonResponse({'success': False, 'message': 'Numéro Mobile Money invalide (format +225xxxxxxxx)'}, status=400)

                # Simulation OTP
                if 'otp_code' not in request.session:
                    # Générer OTP aléatoire (4 chiffres)
                    otp = str(random.randint(1000, 9999))
                    request.session['otp_code'] = otp
                    request.session['mobile_money_operator'] = mobile_money_operator
                    request.session['mobile_money_number'] = mobile_money_number
                    return JsonResponse({
                        'success': False,
                        'message': f'Code OTP envoyé à {mobile_money_number}. Entrez le code à 4 chiffres: {otp} (simulation).',
                        'otp_sent': True
                    })

                # Valider OTP saisi
                if otp_entered == request.session['otp_code']:
                    booking = Booking.objects.create(
                        traveler=traveler,
                        trip=trip,
                        payment_method='mobile_money',
                        reference=f'simulated-mm-{int(timezone.now().timestamp())}',
                        mobile_money_operator=mobile_money_operator,
                        mobile_money_number=mobile_money_number,
                        status='paid'
                    )
                    # Nettoyer la session
                    del request.session['otp_code']
                    del request.session['mobile_money_operator']
                    del request.session['mobile_money_number']
                    del request.session['traveler_id']
                    del request.session['trip_id']
                    messages.success(request, 'Paiement Mobile Money simulé avec succès ! Réservation confirmée.')
                    return JsonResponse({
                        'success': True,
                        'message': 'Paiement Mobile Money simulé avec succès ! Réservation confirmée.',
                        'redirect_url': reverse('pages:booking_success')
                    })
                else:
                    return JsonResponse({'success': False, 'message': 'Code OTP incorrect. Réessayez.'}, status=400)

            return JsonResponse({'success': False, 'message': 'Méthode de paiement non reconnue'}, status=400)

    return render(request, 'pages/booking.html', {
        'trip': trip,
        'user': user,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        'timestamp': int(timezone.now().timestamp()),
        'active_step': 1,
        'Traveler': Traveler,
    })

def booking_success(request):
    return render(request, 'pages/booking_success.html', {'message': 'Votre réservation a été confirmée !'})

# ... autres vues (admin_reviews_view, reply_to_review, delete_review, etc.)
