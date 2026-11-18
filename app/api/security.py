
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader

from app.api.user_store import authenticate_api_key


api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def get_current_user(
    api_key: str | None = Security(api_key_header)
):
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key"
        )

    user = authenticate_api_key(api_key)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return user


def verify_api_key(
    user: dict = Depends(get_current_user)
):
    return user["role"]


def require_admin(
    role: str = Depends(verify_api_key)
):
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return role
