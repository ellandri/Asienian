from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from booking.users.models import User
from django.core.validators import FileExtensionValidator, RegexValidator, URLValidator

class Trip(models.Model):
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=100)
    departure_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = CKEditor5Field('Description', config_name='extends')
    image = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator()],
        help_text="URL d'une image (jpg, jpeg, png, gif)."
    )
    departure_city = models.CharField(max_length=100, blank=True, null=True)
    arrival_city = models.CharField(max_length=100, blank=True, null=True)
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    departure_time = models.TimeField(blank=True, null=True)
    lieux_couverts = CKEditor5Field(blank=True, null=True)
    point_depart = models.CharField(max_length=100, blank=True, null=True)
    point_arrivee = models.CharField(max_length=100, blank=True, null=True)
    is_best_trip = models.BooleanField(default=False)
    points_forts = CKEditor5Field(blank=True, null=True)
    inclusions = CKEditor5Field(blank=True, null=True)
    exclusions = CKEditor5Field(blank=True, null=True)
    politique = CKEditor5Field(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    available_seats = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.destination}"

    class Meta:
        verbose_name = "Voyage"
        verbose_name_plural = "Voyages"

class Traveler(models.Model):
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="traveler")  # Changé en OneToOneField
    title = models.CharField(max_length=10, choices=[
        ('Mr', 'Monsieur'),
        ('Mrs', 'Madame'),
        ('Miss', 'Mademoiselle')
    ])
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    date_of_birth = models.DateField()
    phone_number = models.CharField(
        max_length=15,
        blank=True, null=True,
        validators=[RegexValidator(r'^\+225\d{8,10}$', 'Numéro de téléphone invalide (format +225xxxxxxxx).')]
    )
    nationality = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField(blank=True, null=True)
    profile_photo = models.ImageField(
        upload_to='travelers/',
        blank=True, null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Voyageur"
        verbose_name_plural = "Voyageurs"

class Booking(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('visa_card', 'Carte Visa'),
        ('mobile_money', 'Mobile Money'),
    ]
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('canceled', 'Annulé'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    traveler = models.ForeignKey(Traveler, on_delete=models.CASCADE, related_name="bookings")
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="bookings")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True, unique=True)  # Ajout de unique=True
    card_number = models.CharField(max_length=20, blank=True, null=True)
    card_expiry_month = models.CharField(max_length=2, blank=True, null=True)
    card_expiry_year = models.CharField(max_length=4, blank=True, null=True)
    card_cvv = models.CharField(max_length=4, blank=True, null=True)
    cardholder_name = models.CharField(max_length=100, blank=True, null=True)
    mobile_money_operator = models.CharField(max_length=50, blank=True, null=True)
    mobile_money_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Réservation {self.id} pour {self.traveler} - {self.trip}"

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    trip = models.ForeignKey('Trip', on_delete=models.CASCADE, related_name="reviews", null=True, blank=True)
    rating = models.FloatField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)  # Ajout du champ
    is_deleted = models.BooleanField(default=False)   # Ajout du champ

    def __str__(self):
        return f"Avis de {self.user} sur {self.trip}"

    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"


