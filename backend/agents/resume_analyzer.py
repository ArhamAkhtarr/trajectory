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


# ---------------------------------------------------------------------------
# Fallback data. This is ONLY used when there is no ANTHROPIC_API_KEY, or the
# API call fails outright (network error, malformed response, etc). It is no
# longer used to silently patch/override a valid LLM response, which was the
# main source of "wrong field" analyses before (e.g. a Mechanical Engineer
# resume getting Electrical Engineering skills injected because a keyword
# like "circuit" showed up once).
# ---------------------------------------------------------------------------
DOMAINS = [
    {
        "name": "Electrical Engineering",
        "keywords": [
            "electrical engineer", "electrical engineering", "circuit", "pcb",
            "microcontroller", "embedded", "power systems", "vlsi", "fpga",
            "signal processing", "semiconductor", "high voltage",
            "electromagnetics", "telecom", "arduino", "scada", "multisim",
            "proteus", "ltspice", "hardware engineer",
        ],
        "degree": "Bachelor of Science in Electrical Engineering",
        "skills": [
            "Circuit Design & Analysis", "Power Electronics & Systems",
            "Embedded Microcontrollers", "PCB Design & Layout", "Signal Processing",
        ],
        "tools": ["MATLAB", "Simulink", "Altium Designer", "Proteus", "LTspice", "C/C++", "Keil"],
        "seniority_level": "Electrical Engineer",
        "roles": [
            "Electrical Engineer", "Hardware Systems Engineer", "Power Electronics Engineer",
            "Embedded Systems Engineer", "Control Systems Specialist",
        ],
        "pitch": "Versatile Electrical Engineer specializing in circuit design, power electronics, and hardware system integration based on practical project experience.",
        "key_strengths": [
            "Solid Electrical Engineering academic foundation",
            "Hands-on experience in circuit design and microcontrollers from work history",
            "Proficiency in signal processing and PCB layout tools",
        ],
        "recommendations": [
            "Highlight specific hardware project deliverables and microcontrollers used",
            "Add quantitative specs (e.g. voltage ranges, frequency limits) to experience bullets",
            "Include PCB design tool suite details",
        ],
    },
    {
        "name": "Mechanical Engineering",
        "keywords": [
            "mechanical engineer", "mechanical engineering", "cad", "solidworks",
            "thermodynamics", "fluid mechanics", "autocad", "ansys", "heat transfer",
            "machining", "robotics", "fea", "finite element", "manufacturing",
            "mechatronics", "hvac", "mechanical designer", "thermal engineer",
        ],
        "degree": "Bachelor of Science in Mechanical Engineering",
        "skills": [
            "Computer-Aided Design (CAD)", "Thermodynamics & Heat Transfer",
            "Finite Element Analysis (FEA)", "Mechanical System Design", "Manufacturing Processes",
        ],
        "tools": ["SolidWorks", "AutoCAD", "Ansys", "CATIA", "MATLAB", "CNC Machining"],
        "seniority_level": "Mechanical Engineer",
        "roles": [
            "Mechanical Design Engineer", "Thermal Engineer", "Product Development Engineer",
            "Manufacturing Engineer", "Robotics Systems Specialist",
        ],
        "pitch": "Innovative Mechanical Engineer skilled in 3D CAD modeling, FEA stress analysis, and thermal management systems backed by hands-on engineering accomplishments.",
        "key_strengths": [
            "Strong Mechanical Engineering academic foundation",
            "Proven expertise in 3D CAD modeling and finite element analysis",
            "Practical work experience in thermal systems and manufacturing",
        ],
        "recommendations": [
            "Include CAD assembly complexity and tolerance details from key projects",
            "Quantify thermal/stress load simulation results in career achievements",
            "List rapid prototyping and CNC fabrication experience",
        ],
    },
    {
        "name": "Biomedical Engineering",
        "keywords": [
            "biomedical engineer", "biomedical engineering", "medical device",
            "biomechanics", "biomaterials", "tissue engineering", "medical imaging",
            "biosensors", "prosthetics", "fda", "bioinstrumentation",
            "clinical engineering", "mri", "ultrasound", "biocompatibility",
        ],
        "degree": "Bachelor of Science in Biomedical Engineering",
        "skills": [
            "Medical Device Design", "Biomechanics & Biomaterials", "Biosignal Processing",
            "Regulatory Compliance (FDA/ISO 13485)", "Clinical Instrumentation",
        ],
        "tools": ["MATLAB", "LabVIEW", "SolidWorks", "ImageJ", "Python", "Biopac"],
        "seniority_level": "Biomedical Engineer",
        "roles": [
            "Biomedical Engineer", "Medical Device R&D Engineer", "Clinical Engineer",
            "Biomechanics Specialist", "Bio-Instrumentation Developer",
        ],
        "pitch": "Detail-oriented Biomedical Engineer experienced in medical device prototyping, biosignal processing, and healthcare regulatory compliance.",
        "key_strengths": [
            "Strong Biomedical Science & Engineering background",
            "Hands-on work experience in medical instrumentation and signals",
            "Knowledge of healthcare regulatory standards (ISO 13485 / FDA)",
        ],
        "recommendations": [
            "Highlight ISO 13485 / FDA regulatory compliance exposure in project duties",
            "Quantify biosignal accuracy and clinical testing protocols",
            "Detail specific biomaterial or device testing methodologies",
        ],
    },
    {
        "name": "Civil Engineering",
        "keywords": [
            "civil engineer", "civil engineering", "structural engineer", "concrete",
            "geotechnical", "surveying", "construction management", "revit", "staad",
            "hydraulics", "infrastructure", "transportation", "site engineer",
        ],
        "degree": "Bachelor of Science in Civil Engineering",
        "skills": [
            "Structural Analysis & Design", "Construction Management", "Geotechnical Engineering",
            "Site Surveying", "Infrastructure Planning",
        ],
        "tools": ["AutoCAD", "Revit", "STAAD.Pro", "ETABS", "Primavera P6", "MS Project"],
        "seniority_level": "Civil Engineer",
        "roles": [
            "Civil Engineer", "Structural Engineer", "Construction Project Manager",
            "Geotechnical Engineer", "Site Engineer",
        ],
        "pitch": "Results-driven Civil Engineer specializing in structural analysis, site design, and large-scale construction management based on field project experience.",
        "key_strengths": [
            "Solid Civil & Structural Engineering foundation",
            "Proficiency in BIM software and building codes from work history",
            "Proven construction site coordination skills",
        ],
        "recommendations": [
            "Detail project scope sizes and budget scales managed in experience bullets",
            "Highlight specific structural codes and software used",
            "Add certifications like EIT or PE tracking",
        ],
    },
    {
        "name": "Chemical Engineering",
        "keywords": [
            "chemical engineer", "chemical engineering", "process engineer",
            "reaction kinetics", "aspen", "polymers", "refinery", "mass transfer",
            "thermodynamics", "separation processes", "distillation",
        ],
        "degree": "Bachelor of Science in Chemical Engineering",
        "skills": [
            "Chemical Process Design", "Mass & Energy Balance", "Separation Processes",
            "Reaction Kinetics", "Process Safety Management",
        ],
        "tools": ["Aspen Plus", "HYSYS", "MATLAB", "AutoCAD P&ID", "Excel Solver"],
        "seniority_level": "Chemical Engineer",
        "roles": [
            "Chemical Process Engineer", "Plant Operations Engineer", "R&D Process Specialist",
            "Process Safety Engineer",
        ],
        "pitch": "Process-focused Chemical Engineer skilled in plant optimization, mass transport simulation, and safety protocols based on plant experience.",
        "key_strengths": [
            "Strong Chemical Process & Thermodynamics background",
            "Hands-on work experience with process simulation software",
            "Focus on plant safety and yield optimization",
        ],
        "recommendations": [
            "Quantify process yield improvements and mass balance metrics",
            "Highlight Aspen/HYSYS simulation models created",
            "Include process safety management (PSM) details",
        ],
    },
    {
        "name": "Data Science & AI",
        "keywords": [
            "data scientist", "data science", "machine learning engineer",
            "deep learning", "pandas", "pytorch", "tensorflow", "statistics",
            "scikit-learn", "data analytics", "nlp", "computer vision",
        ],
        "degree": "Bachelor of Science in Data Science / Analytics",
        "skills": [
            "Machine Learning & Deep Learning", "Statistical Data Analysis", "Predictive Modeling",
            "Natural Language Processing", "Big Data Pipeline Design",
        ],
        "tools": ["Python", "PyTorch", "TensorFlow", "Pandas", "Scikit-Learn", "SQL", "Tableau"],
        "seniority_level": "Data Scientist",
        "roles": [
            "Data Scientist", "Machine Learning Engineer", "AI Research Specialist", "Data Analyst",
        ],
        "pitch": "Data Scientist proficient in machine learning architectures, statistical modeling, and data-driven insights demonstrated in work experience.",
        "key_strengths": [
            "Strong mathematical and statistical foundation",
            "Expertise in ML frameworks and data processing",
            "Proven track record of predictive modeling",
        ],
        "recommendations": [
            "Include model accuracy/ROC-AUC metrics from past projects",
            "Detail production deployment of ML models",
            "Highlight feature engineering methodologies",
        ],
    },
    {
        "name": "Software & Computer Engineering",
        "keywords": [
            "software engineer", "software developer", "python developer",
            "full stack engineer", "backend developer", "frontend developer",
            "javascript", "react", "fastapi", "django", "node", "backend",
            "full stack", "frontend", "devops", "cloud", "aws", "kubernetes",
            "database", "computer science",
        ],
        "degree": "Bachelor of Science in Computer Science",
        "skills": [
            "Software Architecture", "API Development", "Database Management",
            "System Design", "Cloud Infrastructure",
        ],
        "tools": ["Python", "JavaScript/TypeScript", "React", "FastAPI", "Docker", "PostgreSQL", "Git"],
        "seniority_level": "Software Engineer",
        "roles": [
            "Software Engineer", "Backend Developer", "Full Stack Engineer", "DevOps Specialist",
        ],
        "pitch": "Versatile Software Engineer with strong background in building scalable APIs and modern web applications across career history.",
        "key_strengths": [
            "Solid Computer Science academic foundation",
            "Multi-stack software engineering proficiency",
            "Experience with modern cloud and API tooling",
        ],
        "recommendations": [
            "Add quantitative performance gains to work history bullets",
            "Detail cloud deployment pipelines and testing suites",
            "Include system architecture diagrams",
        ],
    },
]

# Model used for the analysis call. Kept as one place to update.
ANALYSIS_MODEL = "claude-sonnet-5"

# Resumes longer than this many characters are truncated before being sent to
# the model. This keeps token cost predictable (roughly proportional to
# input length) without hurting accuracy for realistic 1-4 page resumes.
# Raise it if you routinely process very long multi-page CVs.
MAX_RESUME_CHARS = 16000

# Anthropic's Voyage embedding models are used instead of the previous fake
# sine-wave "embedding" (see _generate_embedding docstring below).
VOYAGE_EMBED_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = os.getenv("VOYAGE_EMBED_MODEL", "voyage-3.5")
VOYAGE_DIMENSIONS = int(os.getenv("VOYAGE_EMBED_DIMENSIONS", "1024"))


def _detect_domain_profile(text: str) -> dict:
    """Cheap keyword-matching fallback. Only used when the LLM call is
    unavailable or fails entirely."""
    text_lower = text.lower()

    degree_match = re.search(
        r"\b(bachelor|master|b\.s\.|m\.s\.|b\.e\.|m\.e\.|phd|ph\.d\.|diploma)\s*(of|in)?\s*([A-Za-z\s]{3,40})",
        text,
        re.IGNORECASE,
    )
    extracted_degree = degree_match.group(0).strip().title() if degree_match else None

    best_domain = None
    max_matches = 0
    for domain in DOMAINS:
        matches = sum(1 for kw in domain["keywords"] if kw in text_lower)
        if matches > max_matches:
            max_matches = matches
            best_domain = domain

    if not best_domain or max_matches == 0:
        best_domain = DOMAINS[0]

    return {
        "highest_education": extracted_degree or best_domain["degree"],
        "skills": best_domain["skills"],
        "tools": best_domain["tools"],
        "seniority_level": best_domain["seniority_level"],
        "roles": best_domain["roles"],
        "summary_pitch": best_domain["pitch"],
        "key_strengths": best_domain["key_strengths"],
        "top_recommendations": best_domain["recommendations"],
    }


# ---------------------------------------------------------------------------
# Structured-output schema for the single analysis call. Using a forced tool
# call instead of "please return JSON" + regex code-fence stripping means the
# model literally cannot return malformed JSON, free-text preambles, or
# markdown fences around the answer - Anthropic validates the shape for us.
# ---------------------------------------------------------------------------
RESUME_ANALYSIS_TOOL = {
    "name": "submit_resume_analysis",
    "description": "Submit the structured analysis of a candidate's resume/CV.",
    "input_schema": {
        "type": "object",
        "properties": {
            "highest_education": {
                "type": "string",
                "description": "Exact degree level and major, e.g. 'Bachelor of Science in Civil Engineering'.",
            },
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "4-6 core technical/domain skills evidenced by the work experience and projects, not just listed skills.",
            },
            "tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Software, hardware, languages, or platforms actually used in the candidate's work experience/projects.",
            },
            "seniority_level": {
                "type": "string",
                "description": "Accurate professional title reflecting years of experience and scope, e.g. 'Senior Civil Engineer' or 'Entry-Level Software Engineer'.",
            },
            "suggested_roles": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 5,
                "description": "3-5 job titles this candidate is genuinely qualified for today, grounded in their actual field and experience level.",
            },
            "summary_pitch": {
                "type": "string",
                "description": "A 3-sentence executive candidate profile synthesizing work experience, education, and core skills.",
            },
            "key_strengths": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3,
                "description": "Top 3 strengths, each grounded in a specific piece of evidence from the resume.",
            },
            "top_recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3,
                "description": "Top 3 actionable recommendations to strengthen this specific resume.",
            },
        },
        "required": [
            "highest_education", "skills", "tools", "seniority_level",
            "suggested_roles", "summary_pitch", "key_strengths", "top_recommendations",
        ],
    },
}

ANALYSIS_SYSTEM_PROMPT = """You are an executive career auditor and senior technical recruiter with 20 years \
of experience placing candidates across engineering, software, and data disciplines.

Your job is to read a resume/CV closely and produce an accurate, field-correct analysis. \
The most common mistake to avoid: never infer the candidate's field from a single stray keyword. \
A resume that mentions "circuit" once in a Mechanical Engineering capstone project is NOT an \
Electrical Engineer. Base every judgment on the totality of the WORK EXPERIENCE (titles, duties, \
projects, achievements) read together with the HIGHEST EDUCATION and the TOOLS/SKILLS actually \
used on the job - not on keyword frequency.

If the resume is thin, ambiguous, or clearly not an engineering/technical resume, say so honestly \
in summary_pitch and still fill every field with your best, well-reasoned judgment rather than \
generic filler text.

Call the submit_resume_analysis tool exactly once with your complete analysis."""


def _truncate_resume(resume_text: str) -> str:
    if len(resume_text) <= MAX_RESUME_CHARS:
        return resume_text
    logger.info(
        f"Resume text is {len(resume_text)} chars, truncating to {MAX_RESUME_CHARS} to control token cost."
    )
    return resume_text[:MAX_RESUME_CHARS] + "\n\n[...resume truncated for length...]"


async def _run_llm_analysis(resume_text: str) -> dict | None:
    """Single API call that extracts education/skills/tools/roles/pitch/etc.
    Returns None on any failure so the caller can fall back to heuristics."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    trimmed_resume = _truncate_resume(resume_text)

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model=ANALYSIS_MODEL,
            max_tokens=1800,
            temperature=0.2,
            system=ANALYSIS_SYSTEM_PROMPT,
            tools=[RESUME_ANALYSIS_TOOL],
            tool_choice={"type": "tool", "name": "submit_resume_analysis"},
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this resume/CV:\n\n{trimmed_resume}",
                }
            ],
        )

        for block in message.content:
            if block.type == "tool_use" and block.name == "submit_resume_analysis":
                return dict(block.input)

        logger.error("Model response did not include the expected tool_use block.")
        return None

    except Exception as e:
        logger.error(f"Error calling Anthropic API for resume analysis: {e}")
        return None


def _generate_embedding(text: str) -> list[float]:
    """Deterministic placeholder vector. This is NOT a semantic embedding -
    it is a cheap hash-derived sine sequence used only when no real embedding
    model is configured, so downstream code that expects a fixed-length
    vector doesn't crash. It has no retrieval quality. Set VOYAGE_API_KEY to
    get real, semantically meaningful embeddings instead (see embed_profile)."""
    text_bytes = text.encode("utf-8")
    vec = []
    base_sum = sum(text_bytes)
    for i in range(384):
        val = math.sin(i * 0.1 + base_sum % 50)
        vec.append(round(val, 4))
    return vec


async def _generate_real_embedding(text: str) -> list[float] | None:
    """Calls Voyage AI (Anthropic's recommended embeddings partner) to get a
    real semantic embedding. Returns None on failure/missing key."""
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
    """Runs the single combined LLM analysis call and stores every field
    (including suggested_roles) on state. infer_role reuses suggested_roles
    from here instead of making a second, redundant API call."""
    resume_text = state.get("resume_text", "")
    parsed = await _run_llm_analysis(resume_text)

    if parsed is not None:
        detected_profile = None  # only computed lazily below if needed
        try:
            return {
                "highest_education": str(parsed["highest_education"]),
                "skills": parsed["skills"],
                "tools": parsed["tools"],
                "seniority_level": str(parsed["seniority_level"]),
                "suggested_roles": parsed["suggested_roles"][:5],
                "summary_pitch": str(parsed["summary_pitch"]),
                "key_strengths": parsed["key_strengths"],
                "top_recommendations": parsed["top_recommendations"],
            }
        except KeyError as e:
            logger.error(f"LLM analysis response missing expected field {e}, falling back to heuristics.")

    logger.warning("Falling back to keyword-based heuristic analysis (no API key, or the API call failed).")
    detected_profile = _detect_domain_profile(resume_text)
    return {
        "highest_education": detected_profile["highest_education"],
        "skills": detected_profile["skills"],
        "tools": detected_profile["tools"],
        "seniority_level": detected_profile["seniority_level"],
        "suggested_roles": detected_profile["roles"],
        "summary_pitch": detected_profile["summary_pitch"],
        "key_strengths": detected_profile["key_strengths"],
        "top_recommendations": detected_profile["top_recommendations"],
    }


async def infer_role(state: ResumeState) -> dict:
    """No longer makes its own API call. extract_skills already produced
    field-correct suggested_roles as part of the single combined analysis;
    this node just passes them through (kept as a separate graph node so the
    workflow shape / state keys stay identical for anything downstream)."""
    roles = state.get("suggested_roles")
    if roles:
        return {"suggested_roles": roles[:5]}

    # Defensive fallback in the unlikely case extract_skills didn't set it.
    resume_text = state.get("resume_text", "")
    detected_profile = _detect_domain_profile(resume_text)
    return {"suggested_roles": detected_profile["roles"]}


async def embed_profile(state: ResumeState) -> dict:
    highest_edu = state.get("highest_education", "Engineering Degree")
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
        "highest_education": final_state.get("highest_education", "Engineering Degree"),
        "skills": final_state.get("skills", []),
        "tools": final_state.get("tools", []),
        "suggested_roles": final_state.get("suggested_roles", []),
        "seniority_level": final_state.get("seniority_level", "Engineer"),
        "summary_pitch": final_state.get("summary_pitch", ""),
        "key_strengths": final_state.get("key_strengths", []),
        "top_recommendations": final_state.get("top_recommendations", []),
        "stored_in_supabase": final_state.get("stored_in_supabase", False),
    }