# shared_auth/django_auth.py
from rest_framework import authentication, exceptions
from django.conf import settings
from django.apps import apps
from shared_auth.jwt_handler import decode_access_token


class OnflowJWTAuthentication(authentication.BaseAuthentication):

    def __init__(self):
        user_model_path = getattr(settings, "ONFLOW_AUTH_USER_MODEL", None)
        if user_model_path:
            self.User = apps.get_model(user_model_path)
        else:
            from django.contrib.auth import get_user_model
            self.User = get_user_model()

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split("Bearer ")[1].strip()

        try:
            payload = decode_access_token(token)
            email = payload.get("email")
            if not email:
                raise exceptions.AuthenticationFailed("Invalid token payload")

            user = self.User.objects.filter(email=email).first()
            if not user:
                raise exceptions.AuthenticationFailed("User not found")

            request.auth_payload = payload
            return (user, None)

        except ValueError as e:
            raise exceptions.AuthenticationFailed(str(e))
