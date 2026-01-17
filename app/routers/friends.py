from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional
from app.dependencies import get_current_user, SupabaseUser
from app.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/friends", tags=["friends"])


class FriendRequestCreate(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None


class FriendRequestResponse(BaseModel):
    id: str
    requester_id: str
    recipient_id: str
    status: str
    created_at: str


class NotificationResponse(BaseModel):
    id: str
    type: str
    message: str
    data: Optional[str]
    is_read: bool
    created_at: str


@router.get("/search")
async def search_users(
    q: str = Query("", min_length=1),
    current_user: SupabaseUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()

    response = supabase.table("profiles").select("id, username, profile_picture").ilike("username", f"%{q}%").neq("id", current_user.id).limit(10).execute()

    return [
        {
            "id": user["id"],
            "username": user["username"],
            "profile_picture": user.get("profile_picture"),
        }
        for user in (response.data or [])
    ]


@router.post("/request")
async def create_friend_request(
    payload: FriendRequestCreate,
    current_user: SupabaseUser = Depends(get_current_user),
):
    if not payload.username and not payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or user_id required",
        )

    supabase = get_supabase_admin()

    target_user = None
    if payload.user_id:
        response = supabase.table("profiles").select("*").eq("id", payload.user_id).single().execute()
        target_user = response.data
    if payload.username and not target_user:
        response = supabase.table("profiles").select("*").eq("username", payload.username).single().execute()
        target_user = response.data

    if not target_user or target_user["id"] == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Check for existing friend request
    existing_response = supabase.table("friend_requests").select("*").or_(
        f"and(requester_id.eq.{current_user.id},recipient_id.eq.{target_user['id']}),and(requester_id.eq.{target_user['id']},recipient_id.eq.{current_user.id})"
    ).execute()

    existing = existing_response.data[0] if existing_response.data else None

    if existing and existing.get("status") in ["pending", "accepted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request already exists",
        )

    # Create friend request
    request_response = supabase.table("friend_requests").insert({
        "requester_id": current_user.id,
        "recipient_id": target_user["id"],
        "status": "pending",
    }).execute()

    friend_request = request_response.data[0] if request_response.data else None

    # Create notification
    supabase.table("notifications").insert({
        "user_id": target_user["id"],
        "type": "friend_request",
        "message": f"{current_user.username} sent you a friend request",
        "data": current_user.id,
        "is_read": False,
    }).execute()

    return friend_request


@router.get("/requests")
async def get_friend_requests(
    current_user: SupabaseUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()

    response = supabase.table("friend_requests").select("*").eq("recipient_id", current_user.id).eq("status", "pending").order("created_at", desc=True).execute()

    requests = response.data or []

    # Get requester profiles
    result = []
    for fr in requests:
        profile_response = supabase.table("profiles").select("id, username, profile_picture").eq("id", fr["requester_id"]).single().execute()
        requester = profile_response.data or {}

        result.append({
            "id": fr["id"],
            "requester_id": fr["requester_id"],
            "recipient_id": fr["recipient_id"],
            "status": fr["status"],
            "created_at": fr["created_at"],
            "requester": {
                "id": requester.get("id", fr["requester_id"]),
                "username": requester.get("username", "Unknown"),
                "profile_picture": requester.get("profile_picture"),
            },
        })

    return result


@router.post("/requests/{request_id}/accept")
async def accept_request(
    request_id: str,
    current_user: SupabaseUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()

    response = supabase.table("friend_requests").select("*").eq("id", request_id).eq("recipient_id", current_user.id).single().execute()
    friend_request = response.data

    if not friend_request or friend_request.get("status") != "pending":
        raise HTTPException(status_code=404, detail="Request not found")

    supabase.table("friend_requests").update({
        "status": "accepted",
        "responded_at": datetime.utcnow().isoformat(),
    }).eq("id", request_id).execute()

    # Create notification for requester
    supabase.table("notifications").insert({
        "user_id": friend_request["requester_id"],
        "type": "friend_accept",
        "message": f"{current_user.username} accepted your friend request",
        "data": current_user.id,
        "is_read": False,
    }).execute()

    return {"status": "ok"}


@router.post("/requests/{request_id}/decline")
async def decline_request(
    request_id: str,
    current_user: SupabaseUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()

    response = supabase.table("friend_requests").select("*").eq("id", request_id).eq("recipient_id", current_user.id).single().execute()
    friend_request = response.data

    if not friend_request or friend_request.get("status") != "pending":
        raise HTTPException(status_code=404, detail="Request not found")

    supabase.table("friend_requests").update({
        "status": "declined",
        "responded_at": datetime.utcnow().isoformat(),
    }).eq("id", request_id).execute()

    return {"status": "ok"}


@router.get("/list")
async def list_friends(
    current_user: SupabaseUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()

    response = supabase.table("friend_requests").select("*").eq("status", "accepted").or_(
        f"requester_id.eq.{current_user.id},recipient_id.eq.{current_user.id}"
    ).execute()

    requests = response.data or []

    friend_ids = set()
    for fr in requests:
        if fr["requester_id"] == current_user.id:
            friend_ids.add(fr["recipient_id"])
        else:
            friend_ids.add(fr["requester_id"])

    if not friend_ids:
        return []

    # Fetch friend profiles
    friends = []
    for friend_id in friend_ids:
        profile_response = supabase.table("profiles").select("id, username, profile_picture").eq("id", friend_id).single().execute()
        if profile_response.data:
            friends.append({
                "id": profile_response.data["id"],
                "username": profile_response.data.get("username", "Unknown"),
                "profile_picture": profile_response.data.get("profile_picture"),
            })

    return friends


@router.get("/notifications")
async def get_notifications(
    current_user: SupabaseUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()

    response = supabase.table("notifications").select("*").eq("user_id", current_user.id).order("created_at", desc=True).limit(20).execute()

    notifications = response.data or []

    unread_response = supabase.table("notifications").select("id", count="exact").eq("user_id", current_user.id).eq("is_read", False).execute()
    unread_count = unread_response.count or 0

    return {
        "unread_count": unread_count,
        "items": [
            {
                "id": n["id"],
                "type": n["type"],
                "message": n["message"],
                "data": n.get("data"),
                "is_read": n["is_read"],
                "created_at": n["created_at"],
            }
            for n in notifications
        ],
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: SupabaseUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()

    response = supabase.table("notifications").select("*").eq("id", notification_id).eq("user_id", current_user.id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Notification not found")

    supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()

    return {"status": "ok"}
