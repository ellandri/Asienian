from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from tinymce.models import HTMLField

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
    lieux_couverts = HTMLField(blank=True, null=True)
    point_depart = HTMLField(blank=True, null=True)
    point_arrivee = HTMLField(blank=True, null=True)
    points_forts = HTMLField(blank=True, null=True)
    inclusions = HTMLField(blank=True, null=True)
    exclusions = HTMLField(default="Aucune exclusion", blank=True)
    politique = HTMLField(blank=True, null=True)
    description = HTMLField(blank=True, null=True)

    def __str__(self):
        return f"{self.departure_city} à {self.arrival_city}"

    class Meta:
        verbose_name = "Voyage"
        verbose_name_plural = "Voyages"

class Guest(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    booking_date = models.DateField()
    check_in = models.DateField()
    check_out = models.DateField()
    room_no = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=[('Booked', 'Booked'), ('Pending', 'Pending'), ('Canceled', 'Canceled')])

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
