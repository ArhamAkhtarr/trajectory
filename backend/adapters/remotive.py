import logging
import httpx

try:
    from .utils import clean_text, normalize_date
except ImportError:
    from adapters.utils import clean_text, normalize_date

logger = logging.getLogger(__name__)


async def search_remotive(
    query: str,
    country: str | None = None,
    city: str | None = None,
    page: int = 1,
) -> list[dict]:
    url = "https://remotive.com/api/remote-jobs"
    params = {"search": query}

    headers = {
        "Accept": "application/json",
        "User-Agent": "TrajectoryJobSearchApp/1.0",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        job_list = data.get("jobs", [])
        normalized_jobs: list[dict] = []

        for item in job_list:
            title = clean_text(item.get("title"))
            company = clean_text(item.get("company_name"))
            location = (
                clean_text(item.get("candidate_required_location"))
                or "Worldwide"
            )

            job_dict = {
                "title": title,
                "company": company,
                "location": location,
                "remote": True,
                "url": item.get("url") or "",
                "source": "remotive",
                "posted_date": normalize_date(item.get("publication_date")),
            }
            normalized_jobs.append(job_dict)

        return normalized_jobs

    except Exception as e:
        logger.error(f"Error querying Remotive API: {e}")
        return []
