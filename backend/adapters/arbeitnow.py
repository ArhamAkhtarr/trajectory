import logging
import httpx

try:
    from .utils import clean_text, is_remote_heuristic, normalize_date
except ImportError:
    from adapters.utils import clean_text, is_remote_heuristic, normalize_date

logger = logging.getLogger(__name__)


async def search_arbeitnow(
    query: str,
    country: str | None = None,
    city: str | None = None,
    page: int = 1,
) -> list[dict]:
    url = "https://www.arbeitnow.com/api/job-board-api"
    params = {"page": page}
    headers = {
        "Accept": "application/json",
        "User-Agent": "TrajectoryJobSearchApp/1.0",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        job_list = data.get("data", [])
        query_words = query.lower().split()
        normalized_jobs: list[dict] = []

        for item in job_list:
            title = clean_text(item.get("title"))
            company = clean_text(item.get("company_name"))
            location = clean_text(item.get("location"))
            description = item.get("description") or ""
            tags = " ".join(item.get("tags") or [])

            searchable_text = (
                f"{title} {company} {location} {tags} {description}".lower()
            )

            if query_words and not any(q in searchable_text for q in query_words):
                continue

            remote_flag = bool(item.get("remote")) or is_remote_heuristic(
                title, location, description
            )

            job_dict = {
                "title": title,
                "company": company,
                "location": location,
                "remote": remote_flag,
                "url": item.get("url") or "",
                "source": "arbeitnow",
                "posted_date": normalize_date(item.get("created_at")),
            }
            normalized_jobs.append(job_dict)

        return normalized_jobs

    except Exception as e:
        logger.error(f"Error querying Arbeitnow API: {e}")
        return []
