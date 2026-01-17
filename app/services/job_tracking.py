"""Job tracking service for persisting simulation results using Supabase."""

from datetime import datetime
from app.supabase_client import get_supabase_admin
from app.dependencies import SupabaseUser


def create_job_application(
    user: SupabaseUser,
    company: str,
    role: str,
    difficulty: str,
    job_source: str = "preset",
    location: str = None,
    apply_url: str = None,
    category: str = None,
) -> dict:
    """Create a new job application record."""
    supabase = get_supabase_admin()

    job_data = {
        "user_id": user.id,
        "company": company or "Unknown",
        "role": role,
        "difficulty": difficulty,
        "job_source": job_source,
        "location": location,
        "real_job_apply_url": apply_url,
        "real_job_category": category,
        "current_stage": "screening",
    }

    response = supabase.table("job_applications").insert(job_data).execute()
    job_app = response.data[0] if response.data else None

    if job_app:
        # Update user's total simulations count
        profile_response = supabase.table("user_profiles").select("total_simulations").eq("user_id", user.id).single().execute()
        if profile_response.data:
            current_total = profile_response.data.get("total_simulations", 0)
            supabase.table("user_profiles").update({
                "total_simulations": current_total + 1
            }).eq("user_id", user.id).execute()

    return job_app


def update_screening_result(
    job_app: dict,
    passed: bool,
    feedback: str,
) -> dict:
    """Update job application with screening results."""
    supabase = get_supabase_admin()

    updates = {
        "screening_passed": passed,
        "screening_feedback": feedback,
        "current_stage": "technical" if passed else "result",
    }

    if not passed:
        updates["completed"] = True
        updates["completed_at"] = datetime.utcnow().isoformat()
        updates["final_hired"] = False

    response = supabase.table("job_applications").update(updates).eq("id", job_app["id"]).execute()
    return response.data[0] if response.data else job_app


def update_technical_result(
    job_app: dict,
    passed: bool,
    score: float,
    details: dict = None,
) -> dict:
    """Update job application with technical interview results."""
    supabase = get_supabase_admin()

    updates = {
        "technical_passed": passed,
        "technical_score": score,
        "technical_details": details,
        "current_stage": "behavioral" if passed else "result",
    }

    if not passed:
        updates["completed"] = True
        updates["completed_at"] = datetime.utcnow().isoformat()
        updates["final_hired"] = False

    response = supabase.table("job_applications").update(updates).eq("id", job_app["id"]).execute()
    return response.data[0] if response.data else job_app


def update_behavioral_result(
    job_app: dict,
    passed: bool,
    score: float,
    feedback: str = None,
) -> dict:
    """Update job application with behavioral interview results."""
    supabase = get_supabase_admin()

    updates = {
        "behavioral_passed": passed,
        "behavioral_score": score,
        "behavioral_feedback": feedback,
        "current_stage": "result",
    }

    response = supabase.table("job_applications").update(updates).eq("id", job_app["id"]).execute()
    return response.data[0] if response.data else job_app


def finalize_job_application(
    job_app: dict,
    hired: bool,
    weighted_score: float,
) -> dict:
    """Finalize the job application with final result."""
    supabase = get_supabase_admin()

    updates = {
        "final_hired": hired,
        "final_weighted_score": weighted_score,
        "completed": True,
        "completed_at": datetime.utcnow().isoformat(),
    }

    response = supabase.table("job_applications").update(updates).eq("id", job_app["id"]).execute()

    # Update user's successful simulations if hired
    if hired:
        user_id = job_app.get("user_id")
        profile_response = supabase.table("user_profiles").select("successful_simulations").eq("user_id", user_id).single().execute()
        if profile_response.data:
            current_successful = profile_response.data.get("successful_simulations", 0)
            supabase.table("user_profiles").update({
                "successful_simulations": current_successful + 1
            }).eq("user_id", user_id).execute()

    return response.data[0] if response.data else job_app


def get_job_application(job_id: str, user_id: str) -> dict:
    """Get a job application by ID for a specific user."""
    supabase = get_supabase_admin()
    response = supabase.table("job_applications").select("*").eq("id", job_id).eq("user_id", user_id).single().execute()
    return response.data
