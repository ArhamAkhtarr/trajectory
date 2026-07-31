from datetime import datetime, timezone
import html
import re

COUNTRY_KEYWORDS: dict[str, list[str]] = {
    "us": ["united states", "us", "usa", "america", "united states of america"],
    "gb": ["united kingdom", "uk", "great britain", "england"],
    "ca": ["canada", "ca"],
    "de": ["germany", "deutschland", "de"],
    "pk": ["pakistan", "pk"],
    "in": ["india", "in"],
    "au": ["australia", "au"],
    "fr": ["france", "fr"],
    "nl": ["netherlands", "nl"],
    "sg": ["singapore", "sg"],
    "ae": ["united arab emirates", "uae"],
    "br": ["brazil", "brasil", "br"],
    "jp": ["japan", "jp"],
}


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text_unescaped = html.unescape(str(text))
    cleaned = re.sub(r"<[^>]+>", "", text_unescaped)
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


def is_query_relevant(query: str, title: str, location: str = "") -> bool:
    if not query or not query.strip():
        return True

    q_clean = query.strip().lower()
    title_lower = title.lower()
    location_lower = location.lower()

    if q_clean in title_lower or q_clean in location_lower:
        return True

    # Common software/engineering role broad matchers
    if q_clean in ("engineer", "developer", "software", "tech"):
        broad_terms = ("engineer", "developer", "programmer", "lead", "architect", "manager", "specialist", "coder")
        if any(term in title_lower for term in broad_terms):
            return True

    stopwords = {"a", "an", "the", "and", "or", "in", "for", "at", "with", "job", "jobs"}
    query_tokens = [
        t.lower() for t in re.findall(r"\w+", query)
        if len(t) > 1 and t.lower() not in stopwords
    ]

    if not query_tokens:
        return True

    return any(token in title_lower or token in location_lower for token in query_tokens)


def is_country_relevant(country_code: str, location: str, remote: bool = False) -> bool:
    if not country_code or country_code.lower() in ("all", "global"):
        return True

    c_code = country_code.strip().lower()
    keywords = COUNTRY_KEYWORDS.get(c_code, [c_code])
    loc_lower = location.lower()

    if not loc_lower or "anywhere" in loc_lower or "worldwide" in loc_lower or remote:
        return True

    if any(kw in loc_lower for kw in keywords):
        return True

    return True


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

    try:
        s_clean = s_val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s_clean)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass

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
