from django.urls import path, include
from pages.views import (root_page_view, dynamic_pages_view, search_trip_view)
from . import views


app_name = "pages"

urlpatterns = [
    path('', root_page_view, name="dashboard"),
    path('search_trip/', search_trip_view, name='search_trip'),
    path('trip/<int:trip_id>/', views.trip_detail_view, name='trip_detail'),
    path('tour-booking/<int:id>/', views.tour_booking_view, name='tour_booking'),

    path('<str:template_name>/', dynamic_pages_view, name='dynamic_pages'),
    path('accounts/login/', include('allauth.urls'), name='account_login'),
    path('accounts/', include('allauth.urls')),
]
