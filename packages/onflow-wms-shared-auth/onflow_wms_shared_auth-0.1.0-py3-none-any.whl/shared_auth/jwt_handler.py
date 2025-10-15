# shared_auth/jwt_handler.py
import jwt
from datetime import datetime, timedelta
from django.conf import settings

SECRET_KEY = getattr(settings, "SECRET_KEY")
ALGORITHM = "HS512" 

ACCESS_TOKEN_LIFETIME = getattr(settings, "ACCESS_TOKEN_LIFETIME", timedelta(hours=4))


def create_access_token(payload: dict, expires_delta: timedelta = None):
    to_encode = payload.copy()
    expire = datetime.utcnow() + (expires_delta or ACCESS_TOKEN_LIFETIME)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
    

