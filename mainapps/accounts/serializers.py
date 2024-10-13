# serializers.py
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        # Add custom behavior here before user creation
        user = super().create(validated_data)
        # Add custom logic if needed, such as sending a custom welcome email
        return user
