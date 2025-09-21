from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from booking.pages.views import ModalLoginView, tour_booking_view, booking_process,backup_data_view,dashboard_view,delete_account
from backoffice.views import admin_booking_list_view

urlpatterns = [
    # Django Admin
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("booking.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Custom login view
    path("accounts/login/", ModalLoginView.as_view(), name="account_login"),
    # Backoffice URLs
    path("backoffice/", include("backoffice.urls", namespace="backoffice")),
    # Pages URLs
    path("", include("booking.pages.urls", namespace="pages")),
    # Admin booking list
    path("admin-booking-list/", admin_booking_list_view, name="admin_booking_list_root"),
    # CKEditor URLs
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    # API URLs
    path("api/", include("rest_framework.urls")),
    # Booking URLs
    path("tour-booking/<int:trip_id>/", tour_booking_view, name="tour_booking"),
    path("booking-process/<int:trip_id>/", booking_process, name="bookinga_process"),
    path('account/delete/', delete_account, name='delete_account'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('backup/data/', backup_data_view, name='backup_data'),
]

if settings.DEBUG:
    # Error pages for debugging
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]

    # Debug Toolbar
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]

    # Static and media files in DEBUG mode
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
