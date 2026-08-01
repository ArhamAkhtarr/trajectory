import asyncio
import json
import logging
import math
import os
from typing import TypedDict

import httpx
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from services.ollama_service import clean_json_string, query_ollama

load_dotenv()
logger = logging.getLogger(__name__)


class ResumeState(TypedDict, total=False):
    resume_text: str
    file_reference_id: str
    user_id: str
    highest_education: str
    skills: list[str]
    tools: list[str]
    suggested_roles: list[str]
    seniority_level: str
    summary_pitch: str
    key_strengths: list[str]
    top_recommendations: list[str]
    embedding: list[float]
    stored_in_supabase: bool
    error: str | None


MAX_ANALYSIS_ATTEMPTS = 2
MAX_RESUME_CHARS = 16000

VOYAGE_EMBED_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = os.getenv("VOYAGE_EMBED_MODEL", "voyage-3.5")
VOYAGE_DIMENSIONS = int(os.getenv("VOYAGE_EMBED_DIMENSIONS", "1024"))

ANALYSIS_SYSTEM_PROMPT = """You are an executive career auditor and senior technical recruiter with 20 years \
of experience placing candidates across engineering, software, data, and technical disciplines.
Read the resume closely and produce an accurate, field-correct, candidate-specific analysis in JSON format."""


def _truncate_resume(resume_text: str) -> str:
    if len(resume_text) <= MAX_RESUME_CHARS:
        return resume_text
    logger.info(
        f"Resume text is {len(resume_text)} chars, truncating to {MAX_RESUME_CHARS} to control token cost."
    )
    return resume_text[:MAX_RESUME_CHARS] + "\n\n[...resume truncated for length...]"


async def _run_llm_analysis(resume_text: str) -> tuple[dict | None, str | None]:
    """Runs resume analysis via local Ollama Qwen2.5 3B."""
    if not resume_text or not resume_text.strip():
        return None, "No resume text was provided to analyze."

    trimmed_resume = _truncate_resume(resume_text)

    prompt = f"""Read the resume text below and extract a comprehensive candidate profile.

CRITICAL INSTRUCTION:
Base every judgment on the candidate's WORK EXPERIENCE (duties, projects, job titles), HIGHEST EDUCATION, and TOOLS/SKILLS.
Accurately distinguish their exact engineering field (e.g. Mechanical Engineer vs Civil Engineer vs Electrical Engineer vs Biomedical Engineer vs Software Engineer).

Resume text:
{trimmed_resume}

Return ONLY a valid JSON object matching this EXACT schema:
{{
  "highest_education": "Exact degree level and major (e.g. Bachelor of Science in Civil Engineering)",
  "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4"],
  "tools": ["Tool 1", "Tool 2", "Tool 3"],
  "seniority_level": "Accurate title matching experience and degree (e.g. Senior Civil Engineer)",
  "suggested_roles": ["Job Title 1", "Job Title 2", "Job Title 3"],
  "summary_pitch": "3-sentence executive candidate profile synthesizing work experience, education, and skills.",
  "key_strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "top_recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
}}
"""

    last_error: str | None = None
    for attempt in range(1, MAX_ANALYSIS_ATTEMPTS + 1):
        try:
            raw_resp = await query_ollama(
                prompt=prompt,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                temperature=0.2,
                json_format=True,
                timeout=120.0,
            )

            if not raw_resp:
                last_error = "Ollama returned empty response"
                logger.warning(f"Attempt {attempt}/{MAX_ANALYSIS_ATTEMPTS}: {last_error}")
                continue

            json_str = clean_json_string(raw_resp)
            parsed = json.loads(json_str)

            if isinstance(parsed, dict) and "highest_education" in parsed:
                return parsed, None

            last_error = "Ollama response missing required JSON fields."
            logger.warning(f"Attempt {attempt}/{MAX_ANALYSIS_ATTEMPTS}: {last_error}")

        except Exception as e:
            last_error = f"Error querying Ollama Qwen2.5 3B: {e}"
            logger.error(f"Attempt {attempt}/{MAX_ANALYSIS_ATTEMPTS}: {last_error}")
            await asyncio.sleep(1)

    return None, last_error or "Resume analysis failed via Ollama."


def _empty_analysis(error_message: str) -> dict:
    logger.error(f"Resume analysis failed, returning an empty result: {error_message}")
    return {
        "highest_education": "Unable to determine (analysis failed)",
        "skills": [],
        "tools": [],
        "seniority_level": "Unable to determine (analysis failed)",
        "suggested_roles": [],
        "summary_pitch": f"Automated analysis could not be completed: {error_message}",
        "key_strengths": [],
        "top_recommendations": [
            "Analysis failed - please check if Ollama service is running locally on port 11434."
        ],
        "error": error_message,
    }


def _generate_embedding(text: str) -> list[float]:
    text_bytes = text.encode("utf-8")
    vec = []
    base_sum = sum(text_bytes)
    for i in range(384):
        val = math.sin(i * 0.1 + base_sum % 50)
        vec.append(round(val, 4))
    return vec


async def _generate_real_embedding(text: str) -> list[float] | None:
    voyage_key = os.getenv("VOYAGE_API_KEY")
    if not voyage_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            res = await http_client.post(
                VOYAGE_EMBED_URL,
                headers={
                    "Authorization": f"Bearer {voyage_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": [text],
                    "model": VOYAGE_MODEL,
                    "input_type": "document",
                    "output_dimension": VOYAGE_DIMENSIONS,
                },
            )
            if res.status_code == 200:
                data = res.json()
                return data["data"][0]["embedding"]
            logger.warning(f"Voyage embedding request failed ({res.status_code}): {res.text}")
            return None
    except Exception as e:
        logger.error(f"Error generating Voyage embedding: {e}")
        return None


async def extract_skills(state: ResumeState) -> dict:
    resume_text = state.get("resume_text", "")
    parsed, error = await _run_llm_analysis(resume_text)

    if parsed is None:
        return _empty_analysis(error or "Unknown error")

    try:
        return {
            "highest_education": str(parsed.get("highest_education", "Engineering Degree")),
            "skills": [str(s) for s in parsed.get("skills", [])],
            "tools": [str(t) for t in parsed.get("tools", [])],
            "seniority_level": str(parsed.get("seniority_level", "Engineer")),
            "suggested_roles": [str(r) for r in parsed.get("suggested_roles", [])[:5]],
            "summary_pitch": str(parsed.get("summary_pitch", "")),
            "key_strengths": [str(k) for k in parsed.get("key_strengths", [])],
            "top_recommendations": [str(r) for r in parsed.get("top_recommendations", [])],
            "error": None,
        }
    except Exception as e:
        return _empty_analysis(f"Error parsing Ollama response: {e}")


async def infer_role(state: ResumeState) -> dict:
    return {"suggested_roles": state.get("suggested_roles", [])[:5]}


async def embed_profile(state: ResumeState) -> dict:
    highest_edu = state.get("highest_education", "")
    skills = state.get("skills", [])
    tools = state.get("tools", [])
    roles = state.get("suggested_roles", [])
    pitch = state.get("summary_pitch", "")
    file_ref_id = state.get("file_reference_id", "")
    user_id = state.get("user_id", "default_user")

    profile_text = (
        f"Education: {highest_edu}. Summary: {pitch}. "
        f"Domain Skills: {', '.join(skills)}. Tools: {', '.join(tools)}. "
        f"Qualified Market Roles: {', '.join(roles)}."
    )

    embedding_vec = await _generate_real_embedding(profile_text)
    if embedding_vec is None:
        embedding_vec = _generate_embedding(profile_text)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY")

    stored_in_supabase = False

    if supabase_url and supabase_key:
        table_url = f"{supabase_url.rstrip('/')}/rest/v1/profile_embeddings"
        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "apikey": supabase_key,
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        payload = {
            "file_reference_id": file_ref_id,
            "user_id": user_id,
            "highest_education": highest_edu,
            "skills": skills,
            "tools": tools,
            "suggested_roles": roles,
            "embedding": embedding_vec,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                res = await http_client.post(table_url, json=payload, headers=headers)
                if res.status_code in (200, 201):
                    stored_in_supabase = True
                    logger.info("Successfully stored embedding in Supabase pgvector.")
                else:
                    logger.warning(f"Supabase pgvector insert status {res.status_code}: {res.text}")
        except Exception as ex:
            logger.error(f"Error storing embedding in Supabase: {ex}")

    return {
        "embedding": embedding_vec,
        "stored_in_supabase": stored_in_supabase,
    }


workflow = StateGraph(ResumeState)

workflow.add_node("extract_skills", extract_skills)
workflow.add_node("infer_role", infer_role)
workflow.add_node("embed_profile", embed_profile)

workflow.set_entry_point("extract_skills")
workflow.add_edge("extract_skills", "infer_role")
workflow.add_edge("infer_role", "embed_profile")
workflow.add_edge("embed_profile", END)

resume_analyzer_graph = workflow.compile()


async def analyze_resume_agent(
    file_reference_id: str, resume_text: str, user_id: str = "default_user"
) -> dict:
    initial_state: ResumeState = {
        "file_reference_id": file_reference_id,
        "resume_text": resume_text,
        "user_id": user_id,
    }

    final_state = await resume_analyzer_graph.ainvoke(initial_state)

    return {
        "file_reference_id": final_state.get("file_reference_id"),
        "highest_education": final_state.get("highest_education", ""),
        "skills": final_state.get("skills", []),
        "tools": final_state.get("tools", []),
        "suggested_roles": final_state.get("suggested_roles", []),
        "seniority_level": final_state.get("seniority_level", ""),
        "summary_pitch": final_state.get("summary_pitch", ""),
        "key_strengths": final_state.get("key_strengths", []),
        "top_recommendations": final_state.get("top_recommendations", []),
        "stored_in_supabase": final_state.get("stored_in_supabase", False),
    }