from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from pydantic import BaseModel
from app.dependencies import get_current_user, SupabaseUser
from app.supabase_client import get_supabase_admin
from app.services.job_tracking import (
    create_job_application,
    update_screening_result,
    update_technical_result,
    update_behavioral_result,
    finalize_job_application,
    get_job_application,
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# Request models for job tracking
class CreateJobRequest(BaseModel):
    company: str
    role: str
    difficulty: str
    job_source: str = "preset"
    location: Optional[str] = None
    apply_url: Optional[str] = None
    category: Optional[str] = None


class UpdateScreeningRequest(BaseModel):
    job_id: str
    passed: bool
    feedback: str


class UpdateTechnicalRequest(BaseModel):
    job_id: str
    passed: bool
    score: float
    details: Optional[dict] = None


class UpdateBehavioralRequest(BaseModel):
    job_id: str
    passed: bool
    score: float
    feedback: Optional[str] = None


class FinalizeJobRequest(BaseModel):
    job_id: str
    hired: bool
    weighted_score: float


class JobStatsResponse(BaseModel):
    total_simulations: int
    completed_simulations: int
    successful_simulations: int
    success_rate: float
    by_difficulty: dict


# Job tracking endpoints
@router.post("/track/create")
async def track_create_job(
    request: CreateJobRequest,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Create a new job application to track."""
    job_app = create_job_application(
        user=current_user,
        company=request.company,
        role=request.role,
        difficulty=request.difficulty,
        job_source=request.job_source,
        location=request.location,
        apply_url=request.apply_url,
        category=request.category,
    )
    return job_app


@router.post("/track/screening")
async def track_screening_result(
    request: UpdateScreeningRequest,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Update job application with screening results."""
    job_app = get_job_application(request.job_id, current_user.id)
    if not job_app:
        raise HTTPException(status_code=404, detail="Job application not found")

    job_app = update_screening_result(
        job_app=job_app,
        passed=request.passed,
        feedback=request.feedback,
    )
    return job_app


@router.post("/track/technical")
async def track_technical_result(
    request: UpdateTechnicalRequest,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Update job application with technical interview results."""
    job_app = get_job_application(request.job_id, current_user.id)
    if not job_app:
        raise HTTPException(status_code=404, detail="Job application not found")

    job_app = update_technical_result(
        job_app=job_app,
        passed=request.passed,
        score=request.score,
        details=request.details,
    )
    return job_app


@router.post("/track/behavioral")
async def track_behavioral_result(
    request: UpdateBehavioralRequest,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Update job application with behavioral interview results."""
    job_app = get_job_application(request.job_id, current_user.id)
    if not job_app:
        raise HTTPException(status_code=404, detail="Job application not found")

    job_app = update_behavioral_result(
        job_app=job_app,
        passed=request.passed,
        score=request.score,
        feedback=request.feedback,
    )
    return job_app


@router.post("/track/finalize")
async def track_finalize_job(
    request: FinalizeJobRequest,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Finalize job application with final result."""
    job_app = get_job_application(request.job_id, current_user.id)
    if not job_app:
        raise HTTPException(status_code=404, detail="Job application not found")

    job_app = finalize_job_application(
        job_app=job_app,
        hired=request.hired,
        weighted_score=request.weighted_score,
    )
    return job_app


@router.get("/history")
async def get_job_history(
    status_filter: Optional[str] = None,  # "passed", "rejected", "in_progress"
    limit: int = 50,
    offset: int = 0,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Get user's job application history."""
    supabase = get_supabase_admin()

    query = supabase.table("job_applications").select("*").eq("user_id", current_user.id)

    if status_filter == "passed":
        query = query.eq("final_hired", True)
    elif status_filter == "rejected":
        query = query.eq("completed", True).eq("final_hired", False)
    elif status_filter == "in_progress":
        query = query.eq("completed", False)

    response = query.order("started_at", desc=True).range(offset, offset + limit - 1).execute()
    return response.data or []


@router.get("/history/{job_id}")
async def get_job_details(
    job_id: str,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Get details of a specific job application."""
    job = get_job_application(job_id, current_user.id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found",
        )

    return job


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats(
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Get user's job application statistics."""
    supabase = get_supabase_admin()

    # Get all job applications for the user
    all_jobs_response = supabase.table("job_applications").select("*").eq("user_id", current_user.id).execute()
    all_jobs = all_jobs_response.data or []

    total = len(all_jobs)
    completed = len([j for j in all_jobs if j.get("completed")])
    successful = len([j for j in all_jobs if j.get("final_hired")])

    # Stats by difficulty
    by_difficulty = {}
    for difficulty in ["easy", "medium", "hard"]:
        diff_jobs = [j for j in all_jobs if j.get("difficulty") == difficulty]
        diff_total = len(diff_jobs)
        diff_passed = len([j for j in diff_jobs if j.get("final_hired")])
        by_difficulty[difficulty] = {"total": diff_total, "passed": diff_passed}

    success_rate = (successful / completed * 100) if completed > 0 else 0.0

    return JobStatsResponse(
        total_simulations=total,
        completed_simulations=completed,
        successful_simulations=successful,
        success_rate=round(success_rate, 1),
        by_difficulty=by_difficulty,
    )
