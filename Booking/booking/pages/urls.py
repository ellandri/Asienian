from django.urls import path, include
from django.contrib.auth.views import LogoutView
from pages.views import (
    root_page_view, dynamic_pages_view, search_trip_view, booking_confirm_view,
    my_bookings_view, payment_details_view, add_payment_method_view,
    delete_payment_method_view, edit_payment_method_view, ModalLoginView,
    update_profile_view, trip_detail_view, tour_booking_view, booking_process,booking_success,account_travelers_view,delete_traveler_view
    ,delete_account,dashboard_view,backup_data_view,contact,submit_contact,submit_review,submit_general_review,contact_general
)
from allauth.account.views import LoginView as CustomLoginView
from .views import CustomPasswordResetView

app_name = "pages"

urlpatterns = [
    path('', root_page_view, name="dashboard"),
    path('search_trip/', search_trip_view, name='search_trip'),
    path('trip/<int:trip_id>/', trip_detail_view, name='trip_detail'),
    path('tour-booking/<int:trip_id>/', tour_booking_view, name='tour_booking'),  # Utilise trip_id pour cohérence
    path('booking-process/<int:trip_id>/', booking_process, name='booking_process'),  # Chemin distinct pour booking_process
    path('bookings/success/', booking_success, name='booking_success'),
    path('my-bookings/', my_bookings_view, name='my_bookings'),
    path('account-profile/', update_profile_view, name='account_profile'),
    path('account-travelers/', account_travelers_view, name='account_travelers'),
    path('delete-traveler/<int:traveler_id>/', delete_traveler_view, name='delete_traveler'),
    path('payment-details/', payment_details_view, name='payment_details'),
    path('add-payment-method/', add_payment_method_view, name='add_payment_method'),
    path('delete-payment-method/<int:booking_id>/', delete_payment_method_view, name='delete_payment_method'),
    path('edit-payment-method/<int:booking_id>/', edit_payment_method_view, name='edit_payment_method'),
    path('booking-confirm/<int:booking_id>/', booking_confirm_view, name='booking_confirm'),  # Ajouté ici
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('modal-login/', ModalLoginView.as_view(), name='modal_login'),
    path('accounts/password/reset/', CustomPasswordResetView.as_view(), name='account_reset_password'),
    path('logout/', LogoutView.as_view(next_page='pages:dashboard'), name='logout'),
    path('accounts/', include('allauth.urls')),
    path('account/delete/', delete_account, name='delete_account'),
    path('dashboard/', dashboard_view, name='dashboarddel'),  # Exemple pour la redirection "Conserver mon compte"
    path('backup/data/', backup_data_view, name='backup_data'),  # Exemple pour le lien de sauvegarde
    path('contact/<int:trip_id>/', contact, name='contact'),
    path('trip/<int:trip_id>/review/submit/', submit_review, name='submit_review'),
    path('contact/submit/', submit_contact, name='submit_contact'),
    path('review/submit/', submit_general_review, name='submit_general_review'),

    path('contact/', contact_general, name='contact_general'),
    path('<str:template_name>/', dynamic_pages_view, name='dynamic_pages'),
]
