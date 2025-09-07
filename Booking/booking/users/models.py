from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db import models


class User(AbstractUser):
    """
    Default custom user model for booking.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})


#     # booking/users/models.py
# from django.contrib.auth.models import AbstractUser
# from django.db import models
# from django.urls import reverse
# from django.utils.translation import gettext_lazy as _
#
# class User(AbstractUser):
#     """
#     Default custom user model for booking.
#     """
#     name = models.CharField(_("Name of User"), blank=True, max_length=255)
#     title = models.CharField(max_length=10, choices=[('Mr', 'Mr'), ('Mrs', 'Mrs')], blank=True)
#     first_name = models.CharField(max_length=100, blank=True)
#     last_name = models.CharField(max_length=100, blank=True)
#     date_of_birth = models.DateField(null=True, blank=True)
#     passport_number = models.CharField(max_length=50, unique=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         db_table = 'users_user'
#
#     def get_absolute_url(self) -> str:
#         return reverse("users:detail", kwargs={"username": self.username})

# class Traveler(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travelers')
#     title = models.CharField(max_length=10, choices=[('Mr', 'Mr'), ('Mrs', 'Mrs')])
#     first_name = models.CharField(max_length=100)
#     last_name = models.CharField(max_length=100)
#     date_of_birth = models.DateField()
#     passport_number = models.CharField(max_length=50, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         db_table = 'users_traveler'  # Table séparée pour les voyageurs
#
#     def __str__(self):
#         return f"{self.title} {self.first_name} {self.last_name}"
