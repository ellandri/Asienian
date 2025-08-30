from django import forms
from .models import Trip
import requests

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['departure_city', 'arrival_city', 'vehicle_type', 'duration', 'price', 'rating', 'image', 'departure_time']

    def clean_image(self):
        image_url = self.cleaned_data.get('image')
        if image_url:
            try:
                response = requests.head(image_url)
                content_type = response.headers.get('content-type')
                if not content_type.startswith('image/'):
                    raise forms.ValidationError("L'URL doit pointer vers une image.")
            except requests.RequestException:
                raise forms.ValidationError("L'URL de l'image n'est pas valide.")
        return image_url
