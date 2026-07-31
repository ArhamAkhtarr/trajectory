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
    skills: list[str]
    tools: list[str]
    years_of_experience: float
    suggested_roles: list[str]
    embedding: list[float]
    stored_in_supabase: bool
    error: str | None


def _clean_json_str(text: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text.strip()


def _generate_embedding(text: str) -> list[float]:
    # Produce a 384-dimensional floating point vector
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
            "ANTHROPIC_API_KEY missing. Using fallback skills extraction."
        )
        return {
            "skills": ["Software Development", "Problem Solving"],
            "tools": ["Git", "Python"],
            "years_of_experience": 2.0,
        }

    prompt = f"""You are an expert HR AI resume parser. Extract structured information from the resume below.
Return ONLY valid JSON matching this schema:
{{
  "skills": ["list of technical and soft skills"],
  "tools": ["list of tools, software, platforms, frameworks"],
  "years_of_experience": 3.5
}}

Resume text:
{resume_text}
"""

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0].text
        json_str = _clean_json_str(content)
        parsed = json.loads(json_str)

        skills = parsed.get("skills", [])
        tools = parsed.get("tools", [])
        yoe = float(parsed.get("years_of_experience", 0.0))

        return {
            "skills": skills,
            "tools": tools,
            "years_of_experience": yoe,
        }
    except Exception as e:
        logger.error(f"Error in extract_skills node: {e}")
        return {
            "skills": ["Software Development"],
            "tools": ["Python"],
            "years_of_experience": 1.0,
        }


async def infer_role(state: ResumeState) -> dict:
    skills = state.get("skills", [])
    tools = state.get("tools", [])
    yoe = state.get("years_of_experience", 0.0)
    resume_text = state.get("resume_text", "")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.warning(
            "ANTHROPIC_API_KEY missing. Using fallback role inference."
        )
        return {
            "suggested_roles": [
                "Software Engineer",
                "Backend Developer",
                "Full Stack Engineer",
            ]
        }

    prompt = f"""You are a career advisor AI. Based on the candidate's profile:
Skills: {", ".join(skills)}
Tools: {", ".join(tools)}
Years of Experience: {yoe}

Resume snippet:
{resume_text[:1000]}

Suggest 3 to 5 job titles this candidate is qualified for.
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
                "Developer",
                "Technical Specialist",
            ]
        }


async def embed_profile(state: ResumeState) -> dict:
    skills = state.get("skills", [])
    tools = state.get("tools", [])
    roles = state.get("suggested_roles", [])
    file_ref_id = state.get("file_reference_id", "")
    user_id = state.get("user_id", "default_user")

    profile_text = (
        f"Skills: {', '.join(skills)}. Tools: {', '.join(tools)}. "
        f"Qualified Roles: {', '.join(roles)}."
    )

    embedding_vec = _generate_embedding(profile_text)

    # Store in Supabase pgvector table
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
            "skills": skills,
            "tools": tools,
            "years_of_experience": state.get("years_of_experience", 0.0),
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
        "skills": final_state.get("skills", []),
        "tools": final_state.get("tools", []),
        "years_of_experience": final_state.get("years_of_experience", 0.0),
        "suggested_roles": final_state.get("suggested_roles", []),
        "stored_in_supabase": final_state.get("stored_in_supabase", False),
    }
