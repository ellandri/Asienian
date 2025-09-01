from django import forms
import requests
from .models import Trip

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
