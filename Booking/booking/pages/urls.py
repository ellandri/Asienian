from django.urls import path, include
from pages.views import (root_page_view, dynamic_pages_view)

app_name = "pages"

urlpatterns = [
    path('', root_page_view, name="dashboard"),
    path('<str:template_name>/', dynamic_pages_view, name='dynamic_pages'),
    path('accounts/login/', include('allauth.urls'), name='account_login'),
    path('accounts/', include('allauth.urls')),

]
