from urllib.parse import quote_plus


def build_deeplinks(
    query: str, country: str = "us", city: str | None = None
) -> list[dict]:
    query_str = (query or "").strip()
    query_encoded = quote_plus(query_str)

    # Location string formatting
    loc_parts = []
    if city and city.strip():
        loc_parts.append(city.strip())
    if country and country.strip():
        loc_parts.append(country.strip())
    location_str = ", ".join(loc_parts)
    location_encoded = quote_plus(location_str)

    # LinkedIn Jobs URL
    linkedin_url = (
        f"https://www.linkedin.com/jobs/search/?keywords={query_encoded}"
    )
    if location_encoded:
        linkedin_url += f"&location={location_encoded}"

    # Upwork Jobs Search URL
    upwork_url = f"https://www.upwork.com/nx/search/jobs/?q={query_encoded}"

    # Fiverr Gigs / Services Search URL
    fiverr_url = f"https://www.fiverr.com/search/gigs?query={query_encoded}"

    # Rozee.pk Search URL
    rozee_url = f"https://www.rozee.pk/job/jsearch/q/{query_encoded}"
    if city and city.strip():
        rozee_url += f"/fc/{quote_plus(city.strip())}"

    return [
        {
            "platform": "LinkedIn Jobs",
            "url": linkedin_url,
            "note": "Opens external search",
        },
        {
            "platform": "Upwork",
            "url": upwork_url,
            "note": "Opens external search",
        },
        {
            "platform": "Fiverr",
            "url": fiverr_url,
            "note": "Opens external search",
        },
        {
            "platform": "Rozee.pk",
            "url": rozee_url,
            "note": "Opens external search",
        },
    ]
