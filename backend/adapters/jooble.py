import logging
import os
import httpx
from dotenv import load_dotenv

try:
    from .utils import clean_text, is_remote_heuristic, normalize_date
except ImportError:
    from adapters.utils import clean_text, is_remote_heuristic, normalize_date

load_dotenv()

logger = logging.getLogger(__name__)


async def search_jooble(
    query: str,
    country: str | None = None,
    city: str | None = None,
    page: int = 1,
) -> list[dict]:
    api_key = os.getenv("JOOBLE_API_KEY")
    if not api_key:
        logger.error("JOOBLE_API_KEY is missing in environment variables.")
        return []

    url = f"https://jooble.org/api/{api_key}"

    location_str = ""
    if city and country:
        location_str = f"{city}, {country}"
    elif city:
        location_str = city
    elif country:
        location_str = country

    payload: dict[str, str | int] = {
        "keywords": query,
        "page": page,
    }
    if location_str:
        payload["location"] = location_str

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = data.get("jobs", [])
        normalized_jobs: list[dict] = []

        for item in results:
            title = clean_text(item.get("title"))
            company = clean_text(item.get("company"))
            location = clean_text(item.get("location"))
            snippet = item.get("snippet") or ""

            remote_flag = is_remote_heuristic(title, location, snippet)

            job_dict = {
                "title": title,
                "company": company,
                "location": location,
                "remote": remote_flag,
                "url": item.get("link") or "",
                "source": "jooble",
                "posted_date": normalize_date(item.get("updated")),
            }
            normalized_jobs.append(job_dict)

        return normalized_jobs

    except Exception as e:
        logger.error(f"Error querying Jooble API: {e}")
        return []
