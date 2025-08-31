from django.urls import path, include
from .views import dynamic_pages_view
from rest_framework.routers import DefaultRouter
from .views import login_admin_view, backoffice_view, logout_view
from .views import admin_trips_view, add_trip_form_view, TripViewSet, admin_booking_list_view,trip_detail_view
from . import views




router = DefaultRouter()
router.register(r'trips', TripViewSet, basename='trip')

app_name = 'backoffice'

urlpatterns = [
    path('', login_admin_view, name='backoffice_login'),
    path('dashboard/', backoffice_view, name='backoffice_dashboard'),
    path('api/', include(router.urls)),
    # path('trips/', admin_trips_view, name='admin_trips'),
    path('add-trip-form/', add_trip_form_view, name='admin-add-trip-form'),
    path('admin-booking-list/', views.admin_booking_list_view, name='admin_booking_list'),
    path('admin-guest-list/', views.admin_guest_list_view, name='admin_guest_list'),
    path('<str:template_name>/', dynamic_pages_view, name='dynamic_pages'),
    path('trips/', views.dynamic_pages_view, {'template_name': 'admin-trip-list'}, name='trip-list'),
    path('trip-detail/<int:trip_id>/', trip_detail_view, name='admin-trip-detail'),
    path('logout/', logout_view, name='backoffice_logout'),
    path('admin-agent-detail/<int:user_id>/', views.admin_agent_detail_view, name='admin_agent_detail'),
    path('toggle-best-trip/<int:trip_id>/', views.toggle_best_trip, name='toggle_best_trip'),



]
