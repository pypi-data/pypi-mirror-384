# shared_auth/django_auth.py
from typing import Optional
from rest_framework import authentication, status
from rest_framework.exceptions import APIException
from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model

from shared_auth.jwt_handler import decode_access_token
from shared_auth.config import TOKEN_OPS


class GenericAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "error"

    def __init__(self, detail: str, status_code: Optional[int] = None) -> None:
        super().__init__(detail=detail)
        if status_code is not None:
            self.status_code = status_code


class OnflowJWTAuthentication(authentication.BaseAuthentication):
    STATUS_LOCKED = status.HTTP_423_LOCKED

    def __init__(self):
        user_model_path = getattr(settings, "ONFLOW_AUTH_USER_MODEL", None)
        if user_model_path:
            self.User = apps.get_model(user_model_path)
        else:
            self.User = get_user_model()

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise GenericAPIException(
                detail="Missing or invalid Authorization header.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        token = auth_header.split("Bearer ")[1].strip()

        # ✅ Allow internal system calls to bypass auth if configured
        if TOKEN_OPS and token == TOKEN_OPS:
            return None

        try:
            payload = decode_access_token(token)
        except Exception as e:
            raise GenericAPIException(
                detail=f"Invalid or expired token. ({e})",
                status_code=self.STATUS_LOCKED,
            )

        email = payload.get("email")
        if not email:
            raise GenericAPIException(
                detail="Token payload does not contain a valid user email.",
                status_code=self.STATUS_LOCKED,
            )

        user = self.User.objects.filter(email=email).first()
        if not user:
            raise GenericAPIException(
                detail="User account not found or has been deleted.",
                status_code=self.STATUS_LOCKED,
            )

        if not user.is_active:
            raise GenericAPIException(
                detail="User account is deactivated. Please contact the administrator.",
                status_code=self.STATUS_LOCKED,
            )

        request.auth_payload = payload

        return (user, None)
