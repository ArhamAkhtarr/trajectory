import json
import logging
import math
import os
import re

import anthropic
from adapters.utils import is_remote_heuristic
from agents.resume_analyzer import _generate_embedding

logger = logging.getLogger(__name__)


def _clean_json_str(text: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text.strip()


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


async def rerank_jobs_with_claude(
    user_profile: dict, top_jobs: list[dict]
) -> list[dict]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not top_jobs:
        logger.warning(
            "ANTHROPIC_API_KEY missing or empty top_jobs, skipping Claude re-ranking."
        )
        for j in top_jobs:
            sim = j.get("similarity_score", 0.5)
            j["fit_score"] = int(round(sim * 100))
            j["reasoning"] = "Re-ranked based on profile vector similarity."
        return top_jobs

    jobs_summary = []
    for idx, j in enumerate(top_jobs):
        jobs_summary.append(
            {
                "id": idx,
                "title": j.get("title"),
                "company": j.get("company"),
                "location": j.get("location"),
                "remote": j.get("remote"),
            }
        )

    skills_str = ", ".join(user_profile.get("skills", []))
    tools_str = ", ".join(user_profile.get("tools", []))
    roles_str = ", ".join(user_profile.get("suggested_roles", []))
    yoe = user_profile.get("years_of_experience", 0.0)

    prompt = f"""You are an AI career matchmaking engine. Re-rank the following candidate jobs based on genuine candidate fit, seniority alignment, and skill compatibility, rather than superficial keyword overlap.

Candidate Profile:
- Skills: {skills_str}
- Tools: {tools_str}
- Years of Experience: {yoe}
- Target Roles: {roles_str}

Candidate Jobs (Indices 0 to {len(top_jobs) - 1}):
{json.dumps(jobs_summary, indent=2)}

Return ONLY a valid JSON array of objects re-ranked from best match to worst match:
[
  {{
    "id": 0,
    "fit_score": 95,
    "reasoning": "Brief 1-sentence explanation of why this job fits candidate's seniority and tech stack."
  }},
  ...
]
"""

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text
        json_str = _clean_json_str(content)
        reranked_data = json.loads(json_str)

        reranked_jobs = []
        seen_indices = set()

        if isinstance(reranked_data, list):
            for item in reranked_data:
                idx = item.get("id")
                if (
                    isinstance(idx, int)
                    and 0 <= idx < len(top_jobs)
                    and idx not in seen_indices
                ):
                    seen_indices.add(idx)
                    job_copy = dict(top_jobs[idx])
                    job_copy["fit_score"] = int(item.get("fit_score", 80))
                    job_copy["reasoning"] = str(
                        item.get(
                            "reasoning",
                            "Strong alignment with candidate profile and seniority level.",
                        )
                    )
                    reranked_jobs.append(job_copy)

        for idx, job in enumerate(top_jobs):
            if idx not in seen_indices:
                job_copy = dict(job)
                sim = job_copy.get("similarity_score", 0.5)
                job_copy["fit_score"] = int(round(sim * 100))
                job_copy["reasoning"] = (
                    "Matched based on vector similarity and background."
                )
                reranked_jobs.append(job_copy)

        return reranked_jobs

    except Exception as e:
        logger.error(f"Claude re-ranking error: {e}")
        for j in top_jobs:
            sim = j.get("similarity_score", 0.5)
            j["fit_score"] = int(round(sim * 100))
            j["reasoning"] = "Re-ranked based on profile vector similarity."
        return top_jobs


def compute_matched_jobs(
    resume_profile: dict, all_jobs: list[dict]
) -> list[dict]:
    skills = resume_profile.get("skills", [])
    tools = resume_profile.get("tools", [])
    roles = resume_profile.get("suggested_roles", [])
    skills_text = (
        f"Skills: {', '.join(skills)}. Tools: {', '.join(tools)}. "
        f"Roles: {', '.join(roles)}."
    )

    resume_embedding = resume_profile.get("embedding")
    if not resume_embedding:
        resume_embedding = _generate_embedding(skills_text)

    scored_jobs: list[dict] = []

    for job in all_jobs:
        title = job.get("title", "")
        location = job.get("location", "")
        job_text = f"{title} {location}"
        job_embedding = _generate_embedding(job_text)

        sim = cosine_similarity(resume_embedding, job_embedding)

        job_copy = dict(job)
        job_copy["similarity_score"] = round(sim, 4)
        scored_jobs.append(job_copy)

    # Sort by vector cosine similarity descending
    scored_jobs.sort(key=lambda j: j["similarity_score"], reverse=True)

    # Take top 20
    top_20 = scored_jobs[:20]
    return top_20
