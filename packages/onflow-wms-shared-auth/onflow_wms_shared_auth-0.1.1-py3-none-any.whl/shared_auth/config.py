from datetime import timedelta
import os

SECRET_KEY = os.getenv("ONFLOW_JWT_SECRET", "onflow-shared-secret-key")
ALGORITHM = "HS256"

ACCESS_TOKEN_LIFETIME = timedelta(hours=2)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)
