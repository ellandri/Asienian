from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from booking.users.models import User
from django.core.validators import FileExtensionValidator, RegexValidator

class Trip(models.Model):
    departure_city = models.CharField(max_length=100)
    arrival_city = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=50)
    duration = models.CharField(max_length=20)
    price = models.IntegerField()
    rating = models.FloatField(default=0.0)
    image = models.URLField(max_length=500, blank=True, null=True)
    departure_time = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_best_trip = models.BooleanField(default=False)
    lieux_couverts = CKEditor5Field(blank=True, null=True)
    point_depart = CKEditor5Field(blank=True, null=True)
    point_arrivee = CKEditor5Field(blank=True, null=True)
    points_forts = CKEditor5Field(blank=True, null=True)
    inclusions = CKEditor5Field(blank=True, null=True)
    exclusions = CKEditor5Field(default="Aucune exclusion", blank=True)
    politique = CKEditor5Field(blank=True, null=True)
    description = CKEditor5Field(blank=True, null=True)

    def __str__(self):
        return f"{self.departure_city} à {self.arrival_city}"

    class Meta:
        verbose_name = "Voyage"
        verbose_name_plural = "Voyages"

class Traveler(models.Model):
    TITLE_CHOICES = [
        ('Mr', 'Monsieur'),
        ('Mrs', 'Madame'),
        ('Ms', 'Mademoiselle'),
    ]

    GENDER_CHOICES = [
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('other', 'Autre'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="travelers")
    trip = models.ForeignKey(
        'Trip',  # Utilisez une chaîne pour éviter les importations circulaires
        on_delete=models.CASCADE,
        related_name="travelers",
        null=True,
        blank=True
    )
    title = models.CharField(max_length=10, choices=TITLE_CHOICES, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=False, null=False, default="Inconnu")
    last_name = models.CharField(max_length=100, blank=False, null=False, default="Inconnu")
    date_of_birth = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Le numéro de téléphone doit être au format international, par exemple +1234567890."
        )]
    )
    nationality = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title or ''} {self.first_name} {self.last_name} - {self.trip if self.trip else 'Aucun voyage'}"

    class Meta:
        verbose_name = "Voyageur"
        verbose_name_plural = "Voyageurs"


class Booking(models.Model):
    PAYMENT_METHODS = [
        ('card', 'Credit/Debit Card'),
    ]

    traveler = models.ForeignKey('Traveler', on_delete=models.CASCADE, related_name="bookings")
    trip = models.ForeignKey('Trip', on_delete=models.CASCADE, related_name="bookings")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('canceled', 'Canceled'),
    ], default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True, null=True)
    card_number = models.CharField(max_length=16, blank=True, null=True)
    card_expiry_month = models.CharField(max_length=2, blank=True, null=True)
    card_expiry_year = models.CharField(max_length=4, blank=True, null=True)
    card_cvv = models.CharField(max_length=3, blank=True, null=True)
    cardholder_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.traveler} - {self.trip} ({self.status})"
