from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.dependencies import get_current_user, SupabaseUser

router = APIRouter(prefix="/api/auth", tags=["auth"])


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    profile_picture: Optional[str]
    auth_provider: str
    is_verified: bool
    created_at: Optional[str]


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: SupabaseUser = Depends(get_current_user)):
    """Get current authenticated user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        profile_picture=current_user.profile_picture,
        auth_provider=current_user.auth_provider,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
    )
