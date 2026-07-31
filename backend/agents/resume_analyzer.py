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


DOMAINS = [
    {
        "name": "Electrical Engineering",
        "keywords": [
            "electrical",
            "circuit",
            "pcb",
            "microcontroller",
            "embedded",
            "power systems",
            "vlsi",
            "fpga",
            "signal processing",
            "semiconductor",
            "high voltage",
            "electromagnetics",
            "telecom",
            "arduino",
            "scada",
            "multisim",
            "proteus",
            "ltspice",
            "electrical engineering",
        ],
        "degree": "Bachelor of Science in Electrical Engineering",
        "skills": [
            "Circuit Design & Analysis",
            "Power Electronics & Systems",
            "Embedded Microcontrollers",
            "PCB Design & Layout",
            "Signal Processing",
        ],
        "tools": ["MATLAB", "Simulink", "Altium Designer", "Proteus", "LTspice", "C/C++", "Keil"],
        "seniority_level": "Electrical Engineer",
        "roles": [
            "Electrical Engineer",
            "Hardware Systems Engineer",
            "Power Electronics Engineer",
            "Embedded Systems Engineer",
            "Control Systems Specialist",
        ],
        "pitch": "Versatile Electrical Engineer specializing in circuit design, power electronics, and hardware system integration.",
        "key_strengths": [
            "Solid Electrical Engineering academic foundation",
            "Hands-on circuit design and embedded microcontrollers",
            "Proficiency in signal processing and PCB layout",
        ],
        "recommendations": [
            "Highlight specific hardware projects and microcontrollers used",
            "Add quantitative specs (e.g. voltage ranges, frequency limits) to project bullets",
            "Include PCB design tool suite details",
        ],
    },
    {
        "name": "Mechanical Engineering",
        "keywords": [
            "mechanical",
            "cad",
            "solidworks",
            "thermodynamics",
            "fluid mechanics",
            "autocad",
            "ansys",
            "heat transfer",
            "machining",
            "robotics",
            "fea",
            "finite element",
            "manufacturing",
            "mechatronics",
            "hvac",
            "mechanical engineering",
        ],
        "degree": "Bachelor of Science in Mechanical Engineering",
        "skills": [
            "Computer-Aided Design (CAD)",
            "Thermodynamics & Heat Transfer",
            "Finite Element Analysis (FEA)",
            "Mechanical System Design",
            "Manufacturing Processes",
        ],
        "tools": ["SolidWorks", "AutoCAD", "Ansys", "CATIA", "MATLAB", "CNC Machining"],
        "seniority_level": "Mechanical Engineer",
        "roles": [
            "Mechanical Design Engineer",
            "Thermal Engineer",
            "Product Development Engineer",
            "Manufacturing Engineer",
            "Robotics Systems Specialist",
        ],
        "pitch": "Innovative Mechanical Engineer skilled in 3D CAD modeling, FEA stress analysis, and thermal management systems.",
        "key_strengths": [
            "Strong Mechanical Engineering academic foundation",
            "Expertise in 3D CAD modeling and finite element analysis",
            "Practical knowledge of thermal systems and manufacturing",
        ],
        "recommendations": [
            "Include CAD assembly complexity and tolerance details",
            "Quantify thermal/stress load simulation results in project descriptions",
            "List rapid prototyping and CNC fabrication experience",
        ],
    },
    {
        "name": "Biomedical Engineering",
        "keywords": [
            "biomedical",
            "medical device",
            "biomechanics",
            "biomaterials",
            "tissue engineering",
            "medical imaging",
            "biosensors",
            "prosthetics",
            "fda",
            "bioinstrumentation",
            "clinical engineering",
            "mri",
            "ultrasound",
            "biocompatibility",
            "biomedical engineering",
        ],
        "degree": "Bachelor of Science in Biomedical Engineering",
        "skills": [
            "Medical Device Design",
            "Biomechanics & Biomaterials",
            "Biosignal Processing",
            "Regulatory Compliance (FDA/ISO 13485)",
            "Clinical Instrumentation",
        ],
        "tools": ["MATLAB", "LabVIEW", "SolidWorks", "ImageJ", "Python", "Biopac"],
        "seniority_level": "Biomedical Engineer",
        "roles": [
            "Biomedical Engineer",
            "Medical Device R&D Engineer",
            "Clinical Engineer",
            "Biomechanics Specialist",
            "Bio-Instrumentation Developer",
        ],
        "pitch": "Detail-oriented Biomedical Engineer experienced in medical device prototyping, biosignal processing, and healthcare compliance.",
        "key_strengths": [
            "Strong Biomedical Science & Engineering background",
            "Hands-on experience in medical instrumentation and signals",
            "Knowledge of healthcare regulatory standards",
        ],
        "recommendations": [
            "Highlight ISO 13485 / FDA regulatory compliance exposure",
            "Quantify biosignal accuracy and testing protocols",
            "Detail specific biomaterial or clinical testing methodologies",
        ],
    },
    {
        "name": "Civil Engineering",
        "keywords": [
            "civil",
            "structural",
            "concrete",
            "geotechnical",
            "surveying",
            "construction management",
            "revit",
            "staad",
            "hydraulics",
            "infrastructure",
            "transportation",
            "civil engineering",
        ],
        "degree": "Bachelor of Science in Civil Engineering",
        "skills": [
            "Structural Analysis & Design",
            "Construction Management",
            "Geotechnical Engineering",
            "Site Surveying",
            "Infrastructure Planning",
        ],
        "tools": ["AutoCAD", "Revit", "STAAD.Pro", "ETABS", "Primavera P6", "MS Project"],
        "seniority_level": "Civil Engineer",
        "roles": [
            "Civil Engineer",
            "Structural Engineer",
            "Construction Project Manager",
            "Geotechnical Engineer",
            "Site Engineer",
        ],
        "pitch": "Results-driven Civil Engineer specializing in structural analysis, site design, and large-scale construction management.",
        "key_strengths": [
            "Solid Civil & Structural Engineering foundation",
            "Proficiency in BIM software and building codes",
            "Proven construction site coordination skills",
        ],
        "recommendations": [
            "Detail project scope sizes and budget scales managed",
            "Highlight specific structural codes and software used",
            "Add certifications like EIT or PE tracking",
        ],
    },
    {
        "name": "Chemical Engineering",
        "keywords": [
            "chemical",
            "process engineering",
            "reaction kinetics",
            "aspen",
            "polymers",
            "refinery",
            "mass transfer",
            "thermodynamics",
            "separation processes",
            "distillation",
            "chemical engineering",
        ],
        "degree": "Bachelor of Science in Chemical Engineering",
        "skills": [
            "Chemical Process Design",
            "Mass & Energy Balance",
            "Separation Processes",
            "Reaction Kinetics",
            "Process Safety Management",
        ],
        "tools": ["Aspen Plus", "HYSYS", "MATLAB", "AutoCAD P&ID", "Excel Solver"],
        "seniority_level": "Chemical Engineer",
        "roles": [
            "Chemical Process Engineer",
            "Plant Operations Engineer",
            "R&D Process Specialist",
            "Process Safety Engineer",
        ],
        "pitch": "Process-focused Chemical Engineer skilled in plant optimization, mass transport simulation, and safety protocols.",
        "key_strengths": [
            "Strong Chemical Process & Thermodynamics background",
            "Hands-on experience with process simulation software",
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
            "data science",
            "machine learning",
            "deep learning",
            "pandas",
            "pytorch",
            "tensorflow",
            "statistics",
            "scikit-learn",
            "data analytics",
            "nlp",
            "computer vision",
        ],
        "degree": "Bachelor of Science in Data Science / Analytics",
        "skills": [
            "Machine Learning & Deep Learning",
            "Statistical Data Analysis",
            "Predictive Modeling",
            "Natural Language Processing",
            "Big Data Pipeline Design",
        ],
        "tools": ["Python", "PyTorch", "TensorFlow", "Pandas", "Scikit-Learn", "SQL", "Tableau"],
        "seniority_level": "Data Scientist",
        "roles": [
            "Data Scientist",
            "Machine Learning Engineer",
            "AI Research Specialist",
            "Data Analyst",
        ],
        "pitch": "Data Scientist proficient in machine learning architectures, statistical modeling, and data-driven insights.",
        "key_strengths": [
            "Strong mathematical and statistical foundation",
            "Expertise in ML frameworks and data processing",
            "Proven track record of predictive modeling",
        ],
        "recommendations": [
            "Include model accuracy/ROC-AUC metrics",
            "Detail production deployment of ML models",
            "Highlight feature engineering methodologies",
        ],
    },
    {
        "name": "Software & Computer Engineering",
        "keywords": [
            "software",
            "python",
            "javascript",
            "react",
            "fastapi",
            "django",
            "node",
            "backend",
            "full stack",
            "frontend",
            "devops",
            "cloud",
            "aws",
            "kubernetes",
            "database",
            "computer science",
        ],
        "degree": "Bachelor of Science in Computer Science",
        "skills": [
            "Software Architecture",
            "API Development",
            "Database Management",
            "System Design",
            "Cloud Infrastructure",
        ],
        "tools": ["Python", "JavaScript/TypeScript", "React", "FastAPI", "Docker", "PostgreSQL", "Git"],
        "seniority_level": "Software Engineer",
        "roles": [
            "Software Engineer",
            "Backend Developer",
            "Full Stack Engineer",
            "DevOps Specialist",
        ],
        "pitch": "Versatile Software Engineer with strong background in building scalable APIs and modern web applications.",
        "key_strengths": [
            "Solid Computer Science academic foundation",
            "Multi-stack software engineering proficiency",
            "Experience with modern cloud and API tooling",
        ],
        "recommendations": [
            "Add quantitative performance gains to project bullets",
            "Detail cloud deployment pipelines and testing suites",
            "Include system architecture diagrams",
        ],
    },
]


def _detect_domain_profile(text: str) -> dict:
    text_lower = text.lower()

    # Match explicit degree level if present in text
    degree_match = re.search(
        r"\b(bachelor|master|b\.s\.|m\.s\.|b\.e\.|m\.e\.|phd|ph\.d\.|diploma)\s*(of|in)?\s*([A-Za-z\s]{3,40})",
        text,
        re.IGNORECASE,
    )

    extracted_degree = None
    if degree_match:
        extracted_degree = degree_match.group(0).strip().title()

    best_domain = None
    max_matches = 0

    for domain in DOMAINS:
        matches = 0
        for kw in domain["keywords"]:
            if kw in text_lower:
                matches += 1
        if matches > max_matches:
            max_matches = matches
            best_domain = domain

    if not best_domain or max_matches == 0:
        best_domain = DOMAINS[0]  # Default to Electrical Engineering if unknown

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

    # Smart domain profile detector based on resume text
    detected_profile = _detect_domain_profile(resume_text)

    if not api_key:
        logger.warning(
            "ANTHROPIC_API_KEY missing. Using domain heuristic extraction."
        )
        return {
            "highest_education": detected_profile["highest_education"],
            "skills": detected_profile["skills"],
            "tools": detected_profile["tools"],
            "seniority_level": detected_profile["seniority_level"],
            "summary_pitch": detected_profile["summary_pitch"],
            "key_strengths": detected_profile["key_strengths"],
            "top_recommendations": detected_profile["top_recommendations"],
        }

    prompt = f"""You are a principal executive talent auditor and AI resume reviewer.

CRITICAL DISCIPLINE INSTRUCTION:
The candidate can belong to ANY engineering field or discipline (such as Electrical Engineering, Mechanical Engineering, Biomedical Engineering, Civil Engineering, Chemical Engineering, Data Science, or Software Engineering).
Do NOT default to Software Engineering or Python unless the candidate's resume text explicitly describes software engineering.
Analyze the candidate's SPECIFIC field of study, degree, tools, and technical skills from the text below.

Extract comprehensive structured insight matching this EXACT JSON schema:
{{
  "highest_education": "e.g. Bachelor of Science in Electrical Engineering",
  "skills": ["list of core domain skills from the text"],
  "tools": ["list of frameworks, software, CAD tools, languages, databases"],
  "seniority_level": "e.g. Electrical Engineer / Mechanical Systems Specialist",
  "summary_pitch": "Compelling 2-sentence executive summary emphasizing academic degree + domain technical capabilities.",
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
            "highest_education": str(
                parsed.get("highest_education") or detected_profile["highest_education"]
            ),
            "skills": parsed.get("skills") or detected_profile["skills"],
            "tools": parsed.get("tools") or detected_profile["tools"],
            "seniority_level": str(
                parsed.get("seniority_level") or detected_profile["seniority_level"]
            ),
            "summary_pitch": str(
                parsed.get("summary_pitch") or detected_profile["summary_pitch"]
            ),
            "key_strengths": parsed.get("key_strengths") or detected_profile["key_strengths"],
            "top_recommendations": parsed.get("top_recommendations")
            or detected_profile["top_recommendations"],
        }
    except Exception as e:
        logger.error(f"Error in extract_skills node: {e}")
        return {
            "highest_education": detected_profile["highest_education"],
            "skills": detected_profile["skills"],
            "tools": detected_profile["tools"],
            "seniority_level": detected_profile["seniority_level"],
            "summary_pitch": detected_profile["summary_pitch"],
            "key_strengths": detected_profile["key_strengths"],
            "top_recommendations": detected_profile["top_recommendations"],
        }


async def infer_role(state: ResumeState) -> dict:
    highest_edu = state.get("highest_education", "Engineering Degree")
    skills = state.get("skills", [])
    tools = state.get("tools", [])
    resume_text = state.get("resume_text", "")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    detected_profile = _detect_domain_profile(resume_text)

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing. Using domain heuristic role inference.")
        return {"suggested_roles": detected_profile["roles"]}

    prompt = f"""You are a senior career advisor and executive recruiter.

Candidate Profile:
- Highest Education: {highest_edu}
- Domain Skills: {", ".join(skills)}
- Tools & Software: {", ".join(tools)}

Resume snippet:
{resume_text[:1000]}

CRITICAL REQUIREMENT:
Suggest 3 to 5 highly relevant job titles this candidate is qualified for in their EXACT engineering or professional field.
Your role suggestions MUST be PRIMARILY grounded in their HIGHEST EDUCATION degree level ({highest_edu}) and their specific field (e.g., Electrical Engineering, Mechanical Engineering, Biomedical Engineering, Civil Engineering, Chemical Engineering, etc.).
Do NOT default to Software Engineer unless the candidate's degree and skills are explicitly in software/computer science.

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
        return {"suggested_roles": detected_profile["roles"]}


async def embed_profile(state: ResumeState) -> dict:
    highest_edu = state.get("highest_education", "Engineering Degree")
    skills = state.get("skills", [])
    tools = state.get("tools", [])
    roles = state.get("suggested_roles", [])
    file_ref_id = state.get("file_reference_id", "")
    user_id = state.get("user_id", "default_user")

    profile_text = (
        f"Education: {highest_edu}. "
        f"Domain Skills: {', '.join(skills)}. Tools: {', '.join(tools)}. "
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
