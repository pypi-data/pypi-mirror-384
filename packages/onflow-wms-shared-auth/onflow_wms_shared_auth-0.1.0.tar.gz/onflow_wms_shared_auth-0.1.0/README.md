# Onflow WMS Shared Auth

Thư viện xác thực JWT dùng chung giữa **Django** và **FastAPI**.

## Cài đặt
```bash
pip install git+https://github.com/onflow-tech/onflow-wms-shared-auth.git
```

## Django:

```bash

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "shared_auth.backends_django.OnflowJWTAuthentication",
    ),
}

```

## FastAPI

```bash

from shared_auth.dependencies_fastapi import get_current_user
@app.get("/me")
async def me(user=Depends(get_current_user)):
    return user


```