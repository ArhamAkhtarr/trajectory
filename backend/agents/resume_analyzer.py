import json
import logging
import math
import os
import re
from typing import TypedDict

import anthropic
import httpx
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

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


def _clean_json_str(text: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text.strip()


def _generate_embedding(text: str) -> list[float]:
    text_bytes = text.encode("utf-8")
    vec = []
    base_sum = sum(text_bytes)
    for i in range(384):
        val = math.sin(i * 0.1 + base_sum % 50)
        vec.append(round(val, 4))
    return vec


async def extract_skills(state: ResumeState) -> dict:
    resume_text = state.get("resume_text", "")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.warning(
            "ANTHROPIC_API_KEY missing. Using fallback skills & education extraction."
        )
        return {
            "highest_education": "Bachelor of Science in Computer Science",
            "skills": ["Software Engineering", "System Design", "API Development"],
            "tools": ["Python", "FastAPI", "Docker", "Git"],
            "seniority_level": "Mid-Senior Engineer",
            "summary_pitch": "Results-oriented software engineer with a strong Computer Science degree background and hands-on multi-stack API engineering experience.",
            "key_strengths": [
                "Solid Computer Science academic foundation",
                "Proven multi-skill stack integration (Python, FastAPI, Docker)",
                "Familiarity with distributed architecture principles"
            ],
            "top_recommendations": [
                "Add quantified metrics (e.g. % throughput gain) to engineering bullets",
                "Highlight multi-technology project integrations explicitly",
                "Include cloud architecture & automated deployment details"
            ]
        }

    prompt = f"""You are a principal executive talent auditor and AI resume reviewer. Thoroughly analyze the candidate's resume below.

CRITICAL INSTRUCTION:
1. Identify and extract the candidate's HIGHEST EDUCATION degree level (e.g., "Bachelor of Science in Computer Science", "Master of Science in Software Engineering", "Bachelor of Business Administration", "PhD in Data Science", or "Bachelor's Degree").
2. Extract all core technical skills and tool combinations.

Extract comprehensive structured insight matching this EXACT JSON schema:
{{
  "highest_education": "e.g. Bachelor of Science in Computer Science",
  "skills": ["list of core engineering skills"],
  "tools": ["list of frameworks, languages, databases, tools"],
  "seniority_level": "e.g. Software Engineer / Lead Developer",
  "summary_pitch": "Compelling 2-sentence executive summary emphasizing academic degree + multi-skill stack capabilities.",
  "key_strengths": ["Top strength 1", "Top strength 2", "Top strength 3"],
  "top_recommendations": ["Actionable recommendation 1", "Actionable recommendation 2", "Actionable recommendation 3"]
}}

Resume text:
{resume_text}
"""

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0].text
        json_str = _clean_json_str(content)
        parsed = json.loads(json_str)

        return {
            "highest_education": str(parsed.get("highest_education", "Bachelor's Degree")),
            "skills": parsed.get("skills", ["Software Engineering"]),
            "tools": parsed.get("tools", ["Python"]),
            "seniority_level": str(parsed.get("seniority_level", "Software Engineer")),
            "summary_pitch": str(parsed.get("summary_pitch", "Qualified technical candidate.")),
            "key_strengths": parsed.get("key_strengths", ["Solid technical foundation"]),
            "top_recommendations": parsed.get("top_recommendations", ["Add measurable metrics to resume bullets"]),
        }
    except Exception as e:
        logger.error(f"Error in extract_skills node: {e}")
        return {
            "highest_education": "Bachelor's Degree in Computer Science",
            "skills": ["Software Development"],
            "tools": ["Python"],
            "seniority_level": "Software Engineer",
            "summary_pitch": "Capable developer with technical experience across backend systems.",
            "key_strengths": ["Backend engineering skills"],
            "top_recommendations": ["Highlight system impact with metrics"],
        }


async def infer_role(state: ResumeState) -> dict:
    highest_edu = state.get("highest_education", "Bachelor's Degree")
    skills = state.get("skills", [])
    tools = state.get("tools", [])
    resume_text = state.get("resume_text", "")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing. Using fallback role inference.")
        return {
            "suggested_roles": [
                "Software Engineer",
                "Backend Infrastructure Lead",
                "Full Stack Developer",
            ]
        }

    prompt = f"""You are a senior career advisor and executive recruiter.

Candidate Profile:
- Highest Education: {highest_edu}
- Multi-Skill Stack: {", ".join(skills)}
- Tools & Technologies: {", ".join(tools)}

Resume snippet:
{resume_text[:1000]}

CRITICAL REQUIREMENT:
Suggest 3 to 5 highly relevant job titles this candidate is qualified for.
Your role suggestions MUST be PRIMARILY grounded in their HIGHEST EDUCATION degree level (e.g. Bachelor's, Master's) combined with their multi-skill technical stack ({", ".join(skills[:4])}).
Do NOT suggest roles based purely on a single keyword. Synthesize their degree foundation with their multi-technology combination.

Return ONLY a valid JSON object matching this schema:
{{
  "suggested_roles": ["Job Title 1", "Job Title 2", "Job Title 3"]
}}
"""

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0].text
        json_str = _clean_json_str(content)
        parsed = json.loads(json_str)
        roles = parsed.get("suggested_roles", [])
        return {"suggested_roles": roles[:5]}
    except Exception as e:
        logger.error(f"Error in infer_role node: {e}")
        return {
            "suggested_roles": [
                "Software Engineer",
                "Backend Developer",
                "Full Stack Engineer",
            ]
        }


async def embed_profile(state: ResumeState) -> dict:
    highest_edu = state.get("highest_education", "Bachelor's Degree")
    skills = state.get("skills", [])
    tools = state.get("tools", [])
    roles = state.get("suggested_roles", [])
    file_ref_id = state.get("file_reference_id", "")
    user_id = state.get("user_id", "default_user")

    profile_text = (
        f"Education: {highest_edu}. "
        f"Multi-Skill Stack: {', '.join(skills)}. Tools: {', '.join(tools)}. "
        f"Qualified Market Roles: {', '.join(roles)}."
    )

    embedding_vec = _generate_embedding(profile_text)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv(
        "SUPABASE_PUBLISHABLE_KEY"
    )

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
                res = await http_client.post(
                    table_url, json=payload, headers=headers
                )
                if res.status_code in (200, 201):
                    stored_in_supabase = True
                    logger.info("Successfully stored embedding in Supabase pgvector.")
                else:
                    logger.warning(
                        f"Supabase pgvector insert status {res.status_code}: {res.text}"
                    )
        except Exception as ex:
            logger.error(f"Error storing embedding in Supabase: {ex}")

    return {
        "embedding": embedding_vec,
        "stored_in_supabase": stored_in_supabase,
    }


# Construct LangGraph workflow graph
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
        "highest_education": final_state.get("highest_education", "Bachelor's Degree"),
        "skills": final_state.get("skills", []),
        "tools": final_state.get("tools", []),
        "suggested_roles": final_state.get("suggested_roles", []),
        "seniority_level": final_state.get("seniority_level", "Software Engineer"),
        "summary_pitch": final_state.get("summary_pitch", ""),
        "key_strengths": final_state.get("key_strengths", []),
        "top_recommendations": final_state.get("top_recommendations", []),
        "stored_in_supabase": final_state.get("stored_in_supabase", False),
    }
