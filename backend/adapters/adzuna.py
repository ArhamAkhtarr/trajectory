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


async def search_adzuna(
    query: str, country: str = "us", city: str | None = None, page: int = 1
) -> list[dict]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        logger.error(
            "Adzuna credentials (ADZUNA_APP_ID, ADZUNA_APP_KEY) missing."
        )
        return []

    country_code = (country or "us").strip().lower()
    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/{page}"

    params: dict[str, str | int] = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": 20,
    }

    if city:
        params["where"] = city

    headers = {"Accept": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        normalized_jobs: list[dict] = []

        for item in results:
            title = clean_text(item.get("title"))
            company_info = item.get("company") or {}
            location_info = item.get("location") or {}

            company = clean_text(company_info.get("display_name"))
            location = clean_text(location_info.get("display_name"))
            description = item.get("description") or ""

            remote_flag = is_remote_heuristic(title, location, description)

            job_dict = {
                "title": title,
                "company": company,
                "location": location,
                "remote": remote_flag,
                "url": item.get("redirect_url") or item.get("url") or "",
                "source": "adzuna",
                "posted_date": normalize_date(item.get("created")),
            }
            normalized_jobs.append(job_dict)

        return normalized_jobs

    except Exception as e:
        logger.error(f"Error querying Adzuna API: {e}")
        return []
