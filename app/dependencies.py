from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from app.config import SUPABASE_JWT_SECRET
from app.supabase_client import get_supabase_admin

security = HTTPBearer(auto_error=False)


class SupabaseUser(BaseModel):
    """Represents an authenticated Supabase user."""
    id: str  # UUID as string
    email: str
    username: str
    profile_picture: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    auth_provider: str = "email"
    is_verified: bool = False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> SupabaseUser:
    """Get the current authenticated user from Supabase JWT."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Decode and verify Supabase JWT
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Fetch user profile from Supabase
        supabase = get_supabase_admin()
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()

        profile = profile_response.data if profile_response.data else {}

        # Determine auth provider from app_metadata
        app_metadata = payload.get("app_metadata", {})
        provider = app_metadata.get("provider", "email")

        return SupabaseUser(
            id=user_id,
            email=payload.get("email", ""),
            username=profile.get("username", payload.get("email", "").split("@")[0]),
            profile_picture=profile.get("profile_picture"),
            is_active=profile.get("is_active", True),
            created_at=profile.get("created_at"),
            auth_provider=provider,
            is_verified=payload.get("email_confirmed_at") is not None,
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[SupabaseUser]:
    """Get the current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
