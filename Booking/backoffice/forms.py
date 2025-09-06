from django import forms
import requests
from .models import Trip, Traveler

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'departure_city', 'arrival_city', 'vehicle_type', 'duration', 'price',
            'rating', 'departure_time', 'image', 'lieux_couverts', 'point_depart',
            'point_arrivee', 'is_best_trip', 'description', 'points_forts',
            'inclusions', 'exclusions', 'politique'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'cols': 80, 'rows': 10}),
            'points_forts': forms.Textarea(attrs={'cols': 80, 'rows': 10}),
            'inclusions': forms.Textarea(attrs={'cols': 80, 'rows': 10}),
            'exclusions': forms.Textarea(attrs={'cols': 80, 'rows': 10}),
            'politique': forms.Textarea(attrs={'cols': 80, 'rows': 10}),
            'lieux_couverts': forms.Textarea(attrs={'cols': 80, 'rows': 10}),

        }

class TravelerForm(forms.ModelForm):
    class Meta:
        model = Traveler
        fields = ["title", "first_name", "last_name", "date_of_birth", "email"]
        widgets = {
            "title": forms.Select(attrs={"class": "form-select form-select-sm js-choice border-0"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Prénoms"}),
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control flatpickr", "data-date-format": "d M Y"},
                format="%d %b %Y"
            ),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
        }
