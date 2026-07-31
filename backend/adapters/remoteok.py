import logging
import httpx

try:
    from .utils import clean_text, normalize_date
except ImportError:
    from adapters.utils import clean_text, normalize_date

logger = logging.getLogger(__name__)


async def search_remoteok(
    query: str,
    country: str | None = None,
    city: str | None = None,
    page: int = 1,
) -> list[dict]:
    url = "https://remoteok.com/api"
    headers = {
        "Accept": "application/json",
        "User-Agent": "TrajectoryJobSearchApp/1.0",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, list):
            return []

        job_items = [
            item
            for item in data
            if isinstance(item, dict) and "legal" not in item and "id" in item
        ]

        query_words = query.lower().split()
        normalized_jobs: list[dict] = []

        for item in job_items:
            title = clean_text(item.get("position"))
            company = clean_text(item.get("company"))
            location = clean_text(item.get("location")) or "Worldwide"
            tags = " ".join(item.get("tags") or [])
            description = item.get("description") or ""

            searchable_text = (
                f"{title} {company} {tags} {description}".lower()
            )

            if query_words and not any(q in searchable_text for q in query_words):
                continue

            job_dict = {
                "title": title,
                "company": company,
                "location": location,
                "remote": True,
                "url": item.get("url") or item.get("apply_url") or "",
                "source": "remoteok",
                "posted_date": normalize_date(
                    item.get("date") or item.get("epoch")
                ),
            }
            normalized_jobs.append(job_dict)

        return normalized_jobs

    except Exception as e:
        logger.error(f"Error querying RemoteOK API: {e}")
        return []
