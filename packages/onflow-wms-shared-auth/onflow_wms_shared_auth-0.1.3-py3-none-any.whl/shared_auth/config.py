from datetime import timedelta
import os

SECRET_KEY = "django-insecure-c#lbq#mj3rnia4d=u0@ojdz$#t)g%r_+0m24pxn5pb0hfk_z@3"
ALGORITHM = "HS256"

ACCESS_TOKEN_LIFETIME = timedelta(hours=6)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)
