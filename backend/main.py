import asyncio
import logging
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from adapters import (
    build_deeplinks,
    search_adzuna,
    search_arbeitnow,
    search_jooble,
    search_remoteok,
    search_remotive,
)
from adapters.utils import (
    deduplicate_jobs,
    is_remote_heuristic,
    sort_jobs_by_date,
)
from agents import (
    analyze_resume_agent,
    generate_ideas_agent,
)
from services.matching_service import (
    compute_matched_jobs,
    rerank_jobs_with_claude,
)
from services.resume_service import (
    extract_resume_text,
    upload_file_to_supabase,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trajectory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Memory stores for uploads and analysis results
RESUME_CACHE: dict[str, dict] = {}
ANALYSIS_CACHE: dict[str, dict] = {}


class ResumeAnalyzeRequest(BaseModel):
    file_reference_id: str
    resume_text: str | None = None
    user_id: str = "default_user"


class IdeaGenerateRequest(BaseModel):
    file_reference_id: str | None = None
    skills: list[str] | None = None
    target_roles: list[str] | None = None


async def _safe_search(adapter_fn, query: str, country: str | None, city: str | None, page: int) -> list[dict]:
    try:
        return await adapter_fn(query=query, country=country, city=city, page=page)
    except Exception as e:
        logger.error(f"Adapter {getattr(adapter_fn, '__name__', str(adapter_fn))} failed: {e}")
        return []


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/jobs/search")
async def search_jobs(
    query: str = Query(..., description="Job search query term"),
    country: str | None = Query(default="us", description="Two-letter country code (e.g., us, gb)"),
    city: str | None = Query(default=None, description="City name"),
    mode: str | None = Query(
        default=None, description="Work mode filter: remote, onsite, or hybrid"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
):
    country_val = country if isinstance(country, str) else "us"
    city_val = city if isinstance(city, str) else None
    mode_val = mode if isinstance(mode, str) else None
    page_val = page if isinstance(page, int) and not isinstance(page, bool) else 1

    raw_results = await asyncio.gather(
        _safe_search(search_adzuna, query, country_val, city_val, page_val),
        _safe_search(search_remotive, query, country_val, city_val, page_val),
        _safe_search(search_remoteok, query, country_val, city_val, page_val),
        _safe_search(search_arbeitnow, query, country_val, city_val, page_val),
        _safe_search(search_jooble, query, country_val, city_val, page_val),
        return_exceptions=True,
    )

    merged_jobs: list[dict] = []
    for res in raw_results:
        if isinstance(res, list):
            merged_jobs.extend(res)

    deduped_jobs = deduplicate_jobs(merged_jobs)

    if mode_val:
        m_lower = mode_val.strip().lower()
        filtered_jobs = []

        for job in deduped_jobs:
            title = job.get("title", "")
            location = job.get("location", "")
            is_remote = job.get("remote") is True or is_remote_heuristic(title, location)

            if m_lower == "remote":
                if is_remote:
                    filtered_jobs.append(job)
            elif m_lower == "onsite":
                if not is_remote and "hybrid" not in f"{title} {location}".lower():
                    filtered_jobs.append(job)
            elif m_lower == "hybrid":
                if "hybrid" in f"{title} {location}".lower():
                    filtered_jobs.append(job)
            else:
                filtered_jobs.append(job)

        deduped_jobs = filtered_jobs

    final_jobs = sort_jobs_by_date(deduped_jobs)
    external_links = build_deeplinks(query=query, country=country_val, city=city_val)

    return {
        "jobs": final_jobs,
        "external_links": external_links,
    }


@app.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form(default="default_user"),
):
    if not file.filename:
        raise HTTPException(status_code=422, detail="No file provided.")

    file_bytes = await file.read()
    extracted_text = extract_resume_text(filename=file.filename, file_bytes=file_bytes)
    file_reference_id = str(uuid.uuid4())

    storage_path = await upload_file_to_supabase(
        user_id=user_id,
        file_ref_id=file_reference_id,
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=file.content_type,
    )

    RESUME_CACHE[file_reference_id] = {
        "text": extracted_text,
        "filename": file.filename,
        "user_id": user_id,
        "storage_path": storage_path,
    }

    return {
        "file_reference_id": file_reference_id,
        "text": extracted_text,
        "filename": file.filename,
        "storage_path": storage_path,
    }


@app.post("/resume/analyze")
async def analyze_resume(request: ResumeAnalyzeRequest):
    ref_id = request.file_reference_id
    text = request.resume_text
    user_id = request.user_id

    if not text:
        cached = RESUME_CACHE.get(ref_id)
        if cached:
            text = cached.get("text")
            user_id = cached.get("user_id", user_id)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Resume with file_reference_id '{ref_id}' not found. Please upload first or provide resume_text.",
            )

    result = await analyze_resume_agent(
        file_reference_id=ref_id, resume_text=text, user_id=user_id
    )

    ANALYSIS_CACHE[ref_id] = result

    return result


@app.get("/jobs/matched")
async def get_matched_jobs(
    file_reference_id: str = Query(..., description="File reference ID from resume upload/analyze step"),
    query: str = Query(..., description="Job search query term"),
    country: str | None = Query(default="us", description="Two-letter country code (e.g., us, gb)"),
    city: str | None = Query(default=None, description="City name"),
    mode: str | None = Query(
        default=None, description="Work mode filter: remote, onsite, or hybrid"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
):
    profile = ANALYSIS_CACHE.get(file_reference_id)
    if not profile:
        cached_resume = RESUME_CACHE.get(file_reference_id)
        if cached_resume:
            profile = await analyze_resume_agent(
                file_reference_id=file_reference_id,
                resume_text=cached_resume.get("text", ""),
                user_id=cached_resume.get("user_id", "default_user"),
            )
            ANALYSIS_CACHE[file_reference_id] = profile
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No resume or analysis found for file_reference_id '{file_reference_id}'. Please upload a resume first.",
            )

    search_response = await search_jobs(
        query=query, country=country, city=city, mode=mode, page=page
    )
    all_jobs = search_response.get("jobs", [])

    if not all_jobs:
        return {
            "matched_jobs": [],
            "total_matched": 0,
            "file_reference_id": file_reference_id,
        }

    top_20 = compute_matched_jobs(resume_profile=profile, all_jobs=all_jobs)
    final_matched = await rerank_jobs_with_claude(user_profile=profile, top_jobs=top_20)

    return {
        "matched_jobs": final_matched,
        "total_matched": len(final_matched),
        "file_reference_id": file_reference_id,
    }


@app.post("/ideas/generate")
async def generate_ideas(request: IdeaGenerateRequest):
    ref_id = request.file_reference_id
    skills = request.skills or []
    target_roles = request.target_roles or []

    # If skills or target_roles omitted, look up from analysis cache or trigger analysis
    if (not skills or not target_roles) and ref_id:
        cached_analysis = ANALYSIS_CACHE.get(ref_id)
        if not cached_analysis:
            cached_resume = RESUME_CACHE.get(ref_id)
            if cached_resume:
                cached_analysis = await analyze_resume_agent(
                    file_reference_id=ref_id,
                    resume_text=cached_resume.get("text", ""),
                    user_id=cached_resume.get("user_id", "default_user"),
                )
                ANALYSIS_CACHE[ref_id] = cached_analysis

        if cached_analysis:
            if not skills:
                skills = cached_analysis.get("skills", [])
            if not target_roles:
                target_roles = cached_analysis.get("suggested_roles", [])

    if not skills and not target_roles and not ref_id:
        raise HTTPException(
            status_code=400,
            detail="Please provide 'skills' and 'target_roles', or a valid 'file_reference_id'.",
        )

    result = await generate_ideas_agent(
        skills=skills, target_roles=target_roles, file_reference_id=ref_id
    )

    return result
