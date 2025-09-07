from django.urls import path, include
from django.contrib.auth.views import LogoutView
from pages.views import (root_page_view, dynamic_pages_view, search_trip_view,booking_confirm_view, my_bookings_view, payment_details_view, add_payment_method_view, delete_payment_method_view, edit_payment_method_view, ModalLoginView, update_profile_view, trip_detail_view, tour_booking_view, save_profile)
from . import views
from allauth.account.views import LoginView as CustomLoginView
from .views import CustomPasswordResetView



app_name = "pages"

urlpatterns = [
    path('', root_page_view, name="dashboard"),
    path('search_trip/', search_trip_view, name='search_trip'),
    path('trip/<int:trip_id>/', views.trip_detail_view, name='trip_detail'),
    path('tour-booking/<int:id>/', views.tour_booking_view, name='tour_booking'),
    path('save-profile/', views.save_profile, name='save_profile'),
    path('booking-confirm/<int:booking_id>/', views.booking_confirm_view, name='booking_confirm'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('account-profile/', views.update_profile_view, name='account_profile'),
    path('payment-details/', views.payment_details_view, name='payment_details'),
    path('add-payment-method/', views.add_payment_method_view, name='add_payment_method'),
    path('delete-payment-method/<int:booking_id>/', views.delete_payment_method_view, name='delete_payment_method'),
    path('edit-payment-method/<int:booking_id>/', views.edit_payment_method_view, name='edit_payment_method'),
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('modal-login/', ModalLoginView.as_view(), name='modal_login'),
    path('accounts/password/reset/', CustomPasswordResetView.as_view(), name='account_reset_password'),

    # path('update-password/', update_password_view, name='update_password'),  # Ajouté
    path('logout/', LogoutView.as_view(next_page='pages:dashboard'), name='logout'),
    path('accounts/', include('allauth.urls')),
    path('<str:template_name>/', dynamic_pages_view, name='dynamic_pages'),
]
