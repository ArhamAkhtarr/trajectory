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
                "Distributed Microservice Architecture & Async Processing",
                "CI/CD Automated Pipelines & Infrastructure as Code",
                "Redis In-Memory Caching & Rate-Limiting",
                "Containerization with Docker & Kubernetes Orchestration",
            ]
        }

    prompt = f"""You are an expert tech career strategist. Identify 3 to 6 key technical skill gaps for a candidate.

Current Skills: {", ".join(skills) if skills else "Software Development"}
Target Roles: {", ".join(target_roles) if target_roles else "Software Engineer"}

Identify high-demand, 2026 industry-standard skill gaps or missing competencies required to land and excel in these target roles.
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
                "Distributed Systems Architecture",
                "Docker Containerization & CI/CD",
                "Database Performance & Vector Search",
            ]
        }


def _get_fallback_ideas(skills: list[str], target_roles: list[str]) -> list[dict]:
    primary = skills[0] if skills else "Python"
    field = target_roles[0] if target_roles else "Full Stack Software Engineer"

    return [
        {
            "title": f"High-Throughput {primary} API Gateway & Distributed Cache",
            "description": f"Design and implement an asynchronous API Gateway using {primary} and Redis with token bucket rate limiting and real-time JWT verification.",
            "suggested_stack": [primary, "FastAPI", "Redis", "Docker", "PostgreSQL"],
            "difficulty": "Advanced",
            "estimated_hours": 25,
            "market_relevance": f"In-demand for {field} positions to demonstrate understanding of microservice resiliency, caching, and throughput.",
            "architecture_pipeline": [
                {
                    "phase": "Phase 1: Architecture & Data Ingestion",
                    "tasks": [
                        f"Set up {primary} project with structured logging and OpenAPI spec.",
                        "Configure Redis connection pool with fallback mechanisms."
                    ]
                },
                {
                    "phase": "Phase 2: Middleware & Auth Engine",
                    "tasks": [
                        "Implement Sliding Window Rate Limiter in Redis.",
                        "Create OAuth2 / JWT authentication validation middleware."
                    ]
                },
                {
                    "phase": "Phase 3: Database & Caching Layer",
                    "tasks": [
                        "Integrate PostgreSQL with SQLAlchemy async ORM.",
                        "Add Cache-Aside pattern with TTL expiration on high-traffic endpoints."
                    ]
                },
                {
                    "phase": "Phase 4: Dockerization & CI/CD",
                    "tasks": [
                        "Write multi-stage Dockerfile and docker-compose.yml.",
                        "Configure GitHub Actions pipeline for automated pytest and linting."
                    ]
                }
            ],
            "key_features": [
                "Async non-blocking request routing",
                "Redis sliding window rate-limiting",
                "Sub-10ms cache lookup latency",
                "Automated CI/CD test runner"
            ],
            "repository_structure": [
                "src/main.py",
                "src/middleware/rate_limiter.py",
                "src/cache/redis_client.py",
                "docker-compose.yml",
                ".github/workflows/ci.yml"
            ]
        },
        {
            "title": "Real-time Vector Search & Recommendation Microservice",
            "description": "Build an end-to-end vector embedding service that ingests candidate profiles and performs semantic cosine similarity searches over multi-dimensional vectors.",
            "suggested_stack": [primary, "pgvector", "Supabase", "Anthropic API", "Next.js"],
            "difficulty": "Intermediate",
            "estimated_hours": 20,
            "market_relevance": "Directly aligns with modern AI engineering demands for RAG pipelines and semantic vector retrieval.",
            "architecture_pipeline": [
                {
                    "phase": "Phase 1: Vector Model & Schema",
                    "tasks": [
                        "Configure PostgreSQL with pgvector extension.",
                        "Define vector embedding schema (1536-dim or 384-dim)."
                    ]
                },
                {
                    "phase": "Phase 2: Embedding Generation",
                    "tasks": [
                        "Create LLM embedding generator pipeline.",
                        "Compute cosine distance using pgvector HNSW index."
                    ]
                },
                {
                    "phase": "Phase 3: API & UI Integration",
                    "tasks": [
                        "Expose REST/gRPC endpoint for top-K similarity search.",
                        "Build interactive UI component displaying candidate matches."
                    ]
                }
            ],
            "key_features": [
                "HNSW indexed vector similarity search",
                "Automated LLM re-ranking pipeline",
                "Sub-second semantic search retrieval"
            ],
            "repository_structure": [
                "backend/services/vector_service.py",
                "backend/db/schema.sql",
                "frontend/components/VectorSearch.tsx"
            ]
        }
    ]


async def generate_project_ideas(state: IdeaGeneratorState) -> dict:
    skills = state.get("skills", [])
    target_roles = state.get("target_roles", [])
    skill_gaps = state.get("skill_gaps", [])
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing. Using fallback project ideas.")
        return {"project_ideas": _get_fallback_ideas(skills, target_roles)}

    prompt = f"""You are a world-class principal software architect and career mentor. Generate 4 to 6 highly relevant, in-demand, market-aligned portfolio project ideas for this candidate.

Candidate Profile:
- Skills: {", ".join(skills) if skills else "Software Development"}
- Target Roles: {", ".join(target_roles) if target_roles else "Full Stack Software Engineer"}
- Identified Skill Gaps: {", ".join(skill_gaps)}

CRITICAL REQUIREMENTS:
1. Every project MUST directly reflect current 2026 tech industry demands for {", ".join(target_roles) if target_roles else "Software Engineers"}.
2. Each project MUST include a comprehensive step-by-step implementation pipeline (4 phases), key features list, and repository structure.

Return ONLY a valid JSON object matching this schema:
{{
  "project_ideas": [
    {{
      "title": "Project Title",
      "description": "Clear 2-sentence description of what to build and its commercial/engineering value.",
      "suggested_stack": ["Tech1", "Tech2", "Tech3"],
      "difficulty": "Intermediate",
      "estimated_hours": 25,
      "market_relevance": "Why this project is highly sought after by engineering hiring managers in 2026.",
      "architecture_pipeline": [
        {{
          "phase": "Phase 1: Architecture & Ingestion",
          "tasks": ["Task 1", "Task 2"]
        }},
        {{
          "phase": "Phase 2: Core Processing Engine",
          "tasks": ["Task 1", "Task 2"]
        }},
        {{
          "phase": "Phase 3: Database & Caching",
          "tasks": ["Task 1", "Task 2"]
        }},
        {{
          "phase": "Phase 4: CI/CD & Cloud Deployment",
          "tasks": ["Task 1", "Task 2"]
        }}
      ],
      "key_features": ["Feature 1", "Feature 2", "Feature 3"],
      "repository_structure": ["src/main.py", "src/services/", "docker-compose.yml"]
    }}
  ]
}}
"""

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text
        json_str = _clean_json_str(content)
        parsed = json.loads(json_str)

        raw_ideas = parsed.get("project_ideas", [])
        validated_ideas: list[dict] = []

        for idea in raw_ideas:
            if isinstance(idea, dict):
                pipeline = []
                for p in idea.get("architecture_pipeline", []):
                    if isinstance(p, dict):
                        pipeline.append({
                            "phase": str(p.get("phase", "Implementation Phase")),
                            "tasks": [str(t) for t in p.get("tasks", [])]
                        })
                
                if not pipeline:
                    pipeline = [
                        {"phase": "Phase 1: Setup & Architecture", "tasks": ["Initialize repository", "Define API schema"]},
                        {"phase": "Phase 2: Core Engine", "tasks": ["Implement business logic", "Connect persistence layer"]},
                        {"phase": "Phase 3: Testing & CI/CD", "tasks": ["Write unit tests", "Configure Docker container"]}
                    ]

                validated_ideas.append({
                    "title": str(idea.get("title", "Portfolio Project")),
                    "description": str(idea.get("description", "Practical software engineering project.")),
                    "suggested_stack": [str(s) for s in idea.get("suggested_stack", ["Python", "FastAPI"])],
                    "difficulty": str(idea.get("difficulty", "Intermediate")),
                    "estimated_hours": int(idea.get("estimated_hours", 20)),
                    "market_relevance": str(idea.get("market_relevance", "High market demand for target engineering roles.")),
                    "architecture_pipeline": pipeline,
                    "key_features": [str(f) for f in idea.get("key_features", ["High performance", "Modular code"])],
                    "repository_structure": [str(r) for r in idea.get("repository_structure", ["src/main.py", "docker-compose.yml"])],
                })

        return {"project_ideas": validated_ideas[:6]}

    except Exception as e:
        logger.error(f"Error in generate_project_ideas node: {e}")
        return {"project_ideas": _get_fallback_ideas(skills, target_roles)}


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
