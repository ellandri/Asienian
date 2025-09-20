from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from backoffice.models import Trip, Traveler, Review

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'title', 'destination', 'departure_date', 'departure_city', 'arrival_city',
            'vehicle_type', 'duration', 'price', 'rating', 'departure_time', 'image',
            'lieux_couverts', 'point_depart', 'point_arrivee', 'is_best_trip',
            'description', 'points_forts', 'inclusions', 'exclusions', 'politique',
        ]
        widgets = {
            'description': CKEditor5Widget(attrs={'class': 'django-ckeditor-widget'}, config_name='extends'),
            'points_forts': CKEditor5Widget(attrs={'class': 'django-ckeditor-widget'}, config_name='extends'),
            'inclusions': CKEditor5Widget(attrs={'class': 'django-ckeditor-widget'}, config_name='extends'),
            'exclusions': CKEditor5Widget(attrs={'class': 'django-ckeditor-widget'}, config_name='extends'),
            'politique': CKEditor5Widget(attrs={'class': 'django-ckeditor-widget'}, config_name='extends'),
            'lieux_couverts': CKEditor5Widget(attrs={'class': 'django-ckeditor-widget'}, config_name='extends'),
            'departure_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-modern'}),
            'departure_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-modern'}),
            'image': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://exemple.com/image.jpg'
            }),
            'is_best_trip': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'site_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://exemple.com'}),


        }
        labels = {
            'title': 'Titre du voyage',
            'destination': 'Destination',
            'departure_date': 'Date de départ',
            'departure_city': 'Ville de départ',
            'arrival_city': 'Ville d’arrivée',
            'vehicle_type': 'Type de véhicule',
            'duration': 'Durée',
            'price': 'Prix (FCFA)',
            'rating': 'Note',
            'departure_time': 'Heure de départ',
            'image': 'Lien de l’image',
            'lieux_couverts': 'Lieux couverts',
            'point_depart': 'Point de départ',
            'point_arrivee': 'Point d’arrivée',
            'is_best_trip': 'Meilleur voyage',
            'description': 'Description',
            'points_forts': 'Points forts',
            'inclusions': 'Inclusions',
            'exclusions': 'Exclusions',
            'politique': 'Politique',
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

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'step': 0.5}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'rating': 'Note (1 à 5)',
            'comment': 'Commentaire',
        }
