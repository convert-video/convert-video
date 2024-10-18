# serializers.py
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from djoser.serializers import TokenCreateSerializer
from rest_framework.exceptions import AuthenticationFailed

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

class CustomLoginSerializer(TokenCreateSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Check if both email and password are provided
        if not email or not password:
            raise AuthenticationFailed('No Account Found With The Provided Email Address.')

        # Check if the user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed('This Account Has Already Set Its Initial Password. Please Log In.')

        # Now authenticate the user with the password
        user = authenticate(username=user.username, password=password)

        if not user:
            raise AuthenticationFailed('The Password You Entered Is Incorrect. Please Try Again.')

        # Attach the user object to validated data
        attrs['user'] = user

        return attrs