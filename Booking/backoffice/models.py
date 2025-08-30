from django.db import models

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

    def __str__(self):
        return f"{self.departure_city} à {self.arrival_city}"

    class Meta:
        verbose_name = "Voyage"
        verbose_name_plural = "Voyages"
