import asyncio
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Query

from adapters import (
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

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trajectory API")


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
    # Handle parameter values when called directly in Python vs via FastAPI request runner
    country_val = country if isinstance(country, str) else "us"
    city_val = city if isinstance(city, str) else None
    mode_val = mode if isinstance(mode, str) else None
    page_val = page if isinstance(page, int) and not isinstance(page, bool) else 1

    # Execute all 5 adapters concurrently
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

    # Deduplicate near-duplicate listings (same title + company)
    deduped_jobs = deduplicate_jobs(merged_jobs)

    # Filter by mode if requested
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

    # Sort by posted_date descending
    final_jobs = sort_jobs_by_date(deduped_jobs)

    return final_jobs
