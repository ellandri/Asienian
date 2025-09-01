# booking/users/serializers.py
from rest_framework import serializers
from .models import User
from datetime import datetime

class UserSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(input_formats=['%d %b %Y', '%Y-%m-%d'], allow_null=True)

    class Meta:
        model = User
        fields = ['title', 'first_name', 'last_name', 'date_of_birth', 'passport_number']

    def validate_passport_number(self, value):
        if value and User.objects.filter(passport_number=value).exists():
            raise serializers.ValidationError("Ce numéro de passeport existe déjà.")
        return value

    def validate_date_of_birth(self, value):
        if value and value >= datetime.today().date():
            raise serializers.ValidationError("La date de naissance doit être dans le passé.")
        return value
