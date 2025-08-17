from django.urls import path
from .views import backoffice_view
from .views import login_admin_view
from .views import logout_view

urlpatterns = [
    path('', login_admin_view, name='backoffice_login'),
    path('dashboard/', backoffice_view, name='backoffice_dashboard'),
    path('logout/', logout_view, name='backoffice_logout'),
]
