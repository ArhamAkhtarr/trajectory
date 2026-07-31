from datetime import datetime, timezone
import html
import re


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    # Unescape HTML entities (e.g. &nbsp;, &amp;, &lt;)
    text_unescaped = html.unescape(str(text))
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", "", text_unescaped)
    # Normalize whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


def is_remote_heuristic(
    title: str, location: str, description: str = ""
) -> bool:
    combined = f"{title} {location} {description}".lower()
    keywords = [
        "remote",
        "work from home",
        "wfh",
        "telecommute",
        "anywhere",
        "work-from-home",
        "work from anywhere",
    ]
    return any(kw in combined for kw in keywords)


def normalize_date(date_val: str | int | float | None) -> str:
    if not date_val:
        return ""

    if isinstance(date_val, (int, float)):
        try:
            dt = datetime.fromtimestamp(date_val, tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return ""

    s_val = str(date_val).strip()

    if s_val.isdigit():
        try:
            dt = datetime.fromtimestamp(int(s_val), tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return ""

    # Try ISO parsing
    try:
        s_clean = s_val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s_clean)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass

    # Try common date formats
    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%b %d, %Y",
    ):
        try:
            dt = datetime.strptime(s_val[:19], fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            continue

    return s_val


def normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique_jobs: list[dict] = []

    for job in jobs:
        title_key = normalize_key(job.get("title", ""))
        company_key = normalize_key(job.get("company", ""))
        dedup_key = f"{title_key}:{company_key}"

        if not dedup_key or dedup_key == ":":
            unique_jobs.append(job)
            continue

        if dedup_key not in seen:
            seen.add(dedup_key)
            unique_jobs.append(job)

    return unique_jobs


def sort_jobs_by_date(jobs: list[dict]) -> list[dict]:
    return sorted(
        jobs, key=lambda j: (j.get("posted_date") or ""), reverse=True
    )
