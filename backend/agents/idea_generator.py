import json
import logging
import os
import re
from typing import TypedDict

import anthropic
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

load_dotenv()
logger = logging.getLogger(__name__)


class IdeaGeneratorState(TypedDict, total=False):
    skills: list[str]
    target_roles: list[str]
    file_reference_id: str | None
    skill_gaps: list[str]
    project_ideas: list[dict]
    error: str | None


def _clean_json_str(text: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text.strip()


async def identify_skill_gaps(state: IdeaGeneratorState) -> dict:
    skills = state.get("skills", [])
    target_roles = state.get("target_roles", [])
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.warning(
            "ANTHROPIC_API_KEY missing. Using fallback skill gaps."
        )
        return {
            "skill_gaps": [
                "System Architecture & Microservices",
                "CI/CD Automated Pipelines",
                "Redis Caching & In-Memory Stores",
                "Containerization with Docker & Kubernetes",
            ]
        }

    prompt = f"""You are an expert tech career strategist. Identify skill gaps for a candidate.

Current Skills: {", ".join(skills) if skills else "General Software Development"}
Target Roles: {", ".join(target_roles) if target_roles else "Software Engineer"}

Identify 3 to 6 key technical skill gaps or missing industry-standard competencies required to excel in these target roles.
Return ONLY a valid JSON object matching this schema:
{{
  "skill_gaps": ["Skill Gap 1", "Skill Gap 2", "Skill Gap 3"]
}}
"""

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text
        json_str = _clean_json_str(content)
        parsed = json.loads(json_str)
        gaps = parsed.get("skill_gaps", [])
        return {"skill_gaps": gaps}
    except Exception as e:
        logger.error(f"Error in identify_skill_gaps node: {e}")
        return {
            "skill_gaps": [
                "Distributed System Architecture",
                "Docker Containerization & Deployment",
                "Database Performance Optimization",
            ]
        }


async def generate_project_ideas(state: IdeaGeneratorState) -> dict:
    skills = state.get("skills", [])
    target_roles = state.get("target_roles", [])
    skill_gaps = state.get("skill_gaps", [])
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.warning(
            "ANTHROPIC_API_KEY missing. Using fallback project ideas."
        )
        return {
            "project_ideas": [
                {
                    "title": "High-Throughput API Gateway & Cache Layer",
                    "description": "Design an async API gateway in FastAPI backed by Redis caching and rate-limiting middleware.",
                    "suggested_stack": ["Python", "FastAPI", "Redis", "Docker"],
                    "difficulty": "Intermediate",
                    "estimated_hours": 20,
                },
                {
                    "title": "Automated CI/CD Microservice Monitor",
                    "description": "Build a metrics dashboard that ingests service health events and generates real-time alerts.",
                    "suggested_stack": ["TypeScript", "Next.js", "Docker", "Prometheus"],
                    "difficulty": "Advanced",
                    "estimated_hours": 30,
                },
                {
                    "title": "Vector Resume & Job Recommendation Engine",
                    "description": "Develop a semantic search microservice using embeddings to match candidates with job feeds.",
                    "suggested_stack": ["Python", "FastAPI", "pgvector", "Supabase"],
                    "difficulty": "Intermediate",
                    "estimated_hours": 25,
                },
                {
                    "title": "Distributed Task Scheduler & Worker Pool",
                    "description": "Create a queue-based asynchronous background worker pool for processing document pipelines.",
                    "suggested_stack": ["Python", "Celery", "Redis", "Docker"],
                    "difficulty": "Advanced",
                    "estimated_hours": 35,
                },
                {
                    "title": "Full-Stack Portfolio Analytics Dashboard",
                    "description": "Build an interactive dashboard displaying job application statistics and skill progress.",
                    "suggested_stack": ["React", "Next.js", "Tailwind CSS", "FastAPI"],
                    "difficulty": "Intermediate",
                    "estimated_hours": 20,
                },
            ]
        }

    prompt = f"""You are a senior tech mentor and software architect. Generate 5 to 10 concrete, portfolio-worthy project ideas for this developer.

Candidate Profile:
- Skills: {", ".join(skills) if skills else "Software Engineering"}
- Target Roles: {", ".join(target_roles) if target_roles else "Full Stack Developer"}
- Identified Skill Gaps: {", ".join(skill_gaps)}

Each project idea MUST directly bridge their skill gaps and strengthen their resume for their target roles.

Return ONLY a valid JSON object with a "project_ideas" array where each item matches this schema:
{{
  "project_ideas": [
    {{
      "title": "Project Title",
      "description": "Clear 2-sentence description of what to build and its real-world value.",
      "suggested_stack": ["Tech1", "Tech2", "Tech3"],
      "difficulty": "Intermediate",
      "estimated_hours": 25
    }}
  ]
}}
"""

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text
        json_str = _clean_json_str(content)
        parsed = json.loads(json_str)

        raw_ideas = parsed.get("project_ideas", [])
        validated_ideas: list[dict] = []

        for idea in raw_ideas:
            if isinstance(idea, dict):
                validated_ideas.append(
                    {
                        "title": str(idea.get("title", "Portfolio Project")),
                        "description": str(
                            idea.get("description", "Practical software project.")
                        ),
                        "suggested_stack": list(
                            idea.get("suggested_stack", ["Python", "FastAPI"])
                        ),
                        "difficulty": str(idea.get("difficulty", "Intermediate")),
                        "estimated_hours": int(
                            idea.get("estimated_hours", 20)
                        ),
                    }
                )

        return {"project_ideas": validated_ideas[:10]}

    except Exception as e:
        logger.error(f"Error in generate_project_ideas node: {e}")
        return {
            "project_ideas": [
                {
                    "title": "Async Task Pipeline",
                    "description": "Build an asynchronous worker queue in FastAPI and Redis.",
                    "suggested_stack": ["Python", "FastAPI", "Redis"],
                    "difficulty": "Intermediate",
                    "estimated_hours": 20,
                }
            ]
        }


# Construct LangGraph workflow graph
workflow = StateGraph(IdeaGeneratorState)

workflow.add_node("identify_skill_gaps", identify_skill_gaps)
workflow.add_node("generate_project_ideas", generate_project_ideas)

workflow.set_entry_point("identify_skill_gaps")
workflow.add_edge("identify_skill_gaps", "generate_project_ideas")
workflow.add_edge("generate_project_ideas", END)

idea_generator_graph = workflow.compile()


async def generate_ideas_agent(
    skills: list[str],
    target_roles: list[str],
    file_reference_id: str | None = None,
) -> dict:
    initial_state: IdeaGeneratorState = {
        "skills": skills,
        "target_roles": target_roles,
        "file_reference_id": file_reference_id,
    }

    final_state = await idea_generator_graph.ainvoke(initial_state)

    return {
        "file_reference_id": file_reference_id,
        "skills": skills,
        "target_roles": target_roles,
        "skill_gaps": final_state.get("skill_gaps", []),
        "project_ideas": final_state.get("project_ideas", []),
    }
