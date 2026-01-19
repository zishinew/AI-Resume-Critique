from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from app.dependencies import get_current_user, SupabaseUser
from app.supabase_client import get_supabase_admin
from app.config import SUPABASE_URL
import uuid

router = APIRouter(prefix="/api/users", tags=["users"])

# Supabase Storage bucket name for profile pictures
PROFILE_PICTURES_BUCKET = "profile-pictures"


class ProfileUpdateRequest(BaseModel):
    username: Optional[str] = None
    target_role: Optional[str] = None
    preferred_difficulty: Optional[str] = None


class AccountUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    profile_picture: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    resume_score: Optional[int] = None
    target_role: Optional[str] = None
    preferred_difficulty: str = "medium"
    total_simulations: int = 0
    successful_simulations: int = 0
    updated_at: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    profile_picture: Optional[str] = None
    auth_provider: str = "email"
    is_verified: bool = False
    created_at: Optional[str] = None


@router.get("/profile")
async def get_profile(current_user: SupabaseUser = Depends(get_current_user)):
    """Get current user's profile."""
    supabase = get_supabase_admin()
    response = supabase.table("user_profiles").select("*").eq("user_id", current_user.id).single().execute()

    if not response.data:
        # Create profile if it doesn't exist
        insert_response = supabase.table("user_profiles").insert({
            "user_id": current_user.id
        }).execute()
        return insert_response.data[0] if insert_response.data else {}

    return response.data


@router.put("/profile")
async def update_profile(
    update_data: ProfileUpdateRequest,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Update current user's profile."""
    supabase = get_supabase_admin()

    # Update username in profiles table
    if update_data.username is not None:
        supabase.table("profiles").update({
            "username": update_data.username
        }).eq("id", current_user.id).execute()

    # Update user_profiles table
    updates = {}
    if update_data.target_role is not None:
        updates["target_role"] = update_data.target_role
    if update_data.preferred_difficulty is not None:
        if update_data.preferred_difficulty in ["easy", "medium", "hard"]:
            updates["preferred_difficulty"] = update_data.preferred_difficulty

    if updates:
        response = supabase.table("user_profiles").update(updates).eq("user_id", current_user.id).execute()
        return response.data[0] if response.data else {}

    # Return current profile if no updates
    response = supabase.table("user_profiles").select("*").eq("user_id", current_user.id).single().execute()
    return response.data


@router.get("/me/full")
async def get_full_user_info(current_user: SupabaseUser = Depends(get_current_user)):
    """Get full user info including profile and stats."""
    supabase = get_supabase_admin()

    profile_response = supabase.table("profiles").select("*").eq("id", current_user.id).single().execute()
    user_profile_response = supabase.table("user_profiles").select("*").eq("user_id", current_user.id).single().execute()

    profile = profile_response.data or {}
    user_profile = user_profile_response.data or {}

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": profile.get("username") or current_user.username,
            "profile_picture": profile.get("profile_picture"),
            "auth_provider": current_user.auth_provider,
            "is_verified": current_user.is_verified,
            "created_at": profile.get("created_at"),
        },
        "profile": user_profile,
    }


@router.put("/account")
async def update_account(
    update_data: AccountUpdateRequest,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Update account settings (username, profile picture)."""
    supabase = get_supabase_admin()

    updates = {}
    if update_data.username is not None:
        if not update_data.username.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username cannot be empty",
            )
        updates["username"] = update_data.username.strip()

    if update_data.profile_picture is not None:
        profile_picture = update_data.profile_picture.strip()
        updates["profile_picture"] = profile_picture or None

    if updates:
        supabase.table("profiles").update(updates).eq("id", current_user.id).execute()

    # Return updated profile
    response = supabase.table("profiles").select("*").eq("id", current_user.id).single().execute()
    profile = response.data or {}

    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": profile.get("username", current_user.username),
        "profile_picture": profile.get("profile_picture"),
        "auth_provider": current_user.auth_provider,
        "is_verified": current_user.is_verified,
        "created_at": profile.get("created_at"),
    }


@router.post("/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Upload and update the user's profile picture using Supabase Storage."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are allowed",
        )

    supabase = get_supabase_admin()

    # Generate unique filename
    extension = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "png"
    filename = f"{current_user.id}/{uuid.uuid4().hex}.{extension}"

    # Read file contents
    contents = await file.read()

    # Delete old profile picture if exists
    try:
        # List files in user's folder and delete them
        existing_files = supabase.storage.from_(PROFILE_PICTURES_BUCKET).list(current_user.id)
        if existing_files:
            paths_to_delete = [f"{current_user.id}/{f['name']}" for f in existing_files]
            if paths_to_delete:
                supabase.storage.from_(PROFILE_PICTURES_BUCKET).remove(paths_to_delete)
    except Exception:
        pass  # Ignore errors when deleting old files

    # Upload to Supabase Storage
    try:
        supabase.storage.from_(PROFILE_PICTURES_BUCKET).upload(
            filename,
            contents,
            file_options={"content-type": file.content_type, "upsert": "true"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}",
        )

    # Get public URL
    profile_picture_url = f"{SUPABASE_URL}/storage/v1/object/public/{PROFILE_PICTURES_BUCKET}/{filename}"

    # Update profile with new picture URL
    supabase.table("profiles").update({
        "profile_picture": profile_picture_url
    }).eq("id", current_user.id).execute()

    # Return updated user info
    response = supabase.table("profiles").select("*").eq("id", current_user.id).single().execute()
    profile = response.data or {}

    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": profile.get("username", current_user.username),
        "profile_picture": profile.get("profile_picture"),
        "auth_provider": current_user.auth_provider,
        "is_verified": current_user.is_verified,
        "created_at": profile.get("created_at"),
    }
