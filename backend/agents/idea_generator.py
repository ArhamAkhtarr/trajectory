import asyncio
import json
import logging
import os
import re
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from services.ollama_service import clean_json_string, query_ollama

load_dotenv()
logger = logging.getLogger(__name__)


class IdeaGeneratorState(TypedDict, total=False):
    highest_education: str
    skills: list[str]
    target_roles: list[str]
    file_reference_id: str | None
    live_market_insights: list[str]
    skill_gaps: list[str]
    project_ideas: list[dict]
    error: str | None


DOMAIN_GAP_FALLBACKS = {
    "electrical": [
        "Embedded Real-Time Operating Systems (FreeRTOS / Zephyr)",
        "High-Speed Digital PCB Layout & EMI/EMC Mitigation",
        "Automotive CAN / LIN Bus Communication Protocols",
        "FPGA Hardware Acceleration with Verilog / VHDL",
    ],
    "mechanical": [
        "Computational Fluid Dynamics (CFD Aerodynamic Simulation)",
        "Additive Manufacturing & 3D Topology Optimization",
        "ASME Y14.5 Geometric Dimensioning & Tolerancing (GD&T)",
        "Electro-Mechanical Actuators & Mechatronic Control Loops",
    ],
    "biomedical": [
        "ISO 14971 Medical Device Risk Management",
        "Biocompatible Polymer Processing & Microfluidics",
        "FDA 510(k) Pre-Market Regulatory Submissions",
        "Wearable Biosensor Signal Filtering & Noise Reduction",
    ],
    "civil": [
        "Building Information Modeling (4D/5D BIM Coordination)",
        "Geotechnical Slope Stability & Soil-Structure Interaction",
        "Sustainable Green Building & LEED Energy Compliance",
        "Seismic Structural Design & Earthquake Engineering",
    ],
    "chemical": [
        "Dynamic Process Simulation & Control in Aspen HYSYS",
        "HAZOP Industrial Process Safety & Risk Assessment",
        "Catalytic Reaction Kinetics & Polymer Processing",
        "Bioprocess Scaling & Membrane Separation Systems",
    ],
    "software": [
        "Asynchronous Distributed Microservices & Event Streaming",
        "High-Performance Vector Indexing (HNSW) & RAG",
        "Kubernetes Container Orchestration & Infrastructure as Code",
        "Redis Rate-Limiting & High-Throughput In-Memory Caching",
    ],
}


def _get_domain_gaps(highest_edu: str, skills: list[str], target_roles: list[str]) -> list[str]:
    combined = f"{highest_edu} {' '.join(skills)} {' '.join(target_roles)}".lower()
    for key, gaps in DOMAIN_GAP_FALLBACKS.items():
        if key in combined:
            return gaps
    return DOMAIN_GAP_FALLBACKS["electrical"]


def _get_domain_project_fallback(highest_edu: str, skills: list[str], target_roles: list[str]) -> list[dict]:
    combined = f"{highest_edu} {' '.join(skills)} {' '.join(target_roles)}".lower()

    if "mechanical" in combined:
        return [
            {
                "title": "Autonomous Robotic Arm with FEA & Thermal Analysis",
                "description": "Design an electro-mechanical robotic arm using SolidWorks 3D CAD modeling, perform Ansys FEA stress simulations on joints, and implement motor driver control circuits.",
                "suggested_stack": ["SolidWorks", "Ansys FEA", "MATLAB", "Arduino/C++", "3D Printing"],
                "difficulty": "Advanced",
                "estimated_hours": 30,
                "market_relevance": f"Directly requested in live Mechanical Engineering job ads for structural load simulation, CAD assembly, and mechatronic control.",
                "architecture_pipeline": [
                    {
                        "phase": "Phase 1: CAD Kinematic Modeling",
                        "tasks": ["3D CAD assembly in SolidWorks", "Define joint constraints and motion range"]
                    },
                    {
                        "phase": "Phase 2: FEA Stress & Thermal Simulation",
                        "tasks": ["Apply von Mises stress mesh in Ansys", "Optimize structural wall thickness"]
                    },
                    {
                        "phase": "Phase 3: Motor & Circuit Assembly",
                        "tasks": ["Wire stepper motor drivers", "Program PID positioning loop in MATLAB/C++"]
                    },
                    {
                        "phase": "Phase 4: Prototyping & Testing",
                        "tasks": ["Rapid 3D print components", "Calibrate load deflection tolerances"]
                    }
                ],
                "key_features": ["3D CAD parametric assembly", "Ansys FEA structural optimization", "Closed-loop PID position control"],
                "repository_structure": ["cad/robot_arm.sldasm", "simulation/ansys_stress.wbpj", "firmware/main.cpp"]
            }
        ]
    elif "biomedical" in combined:
        return [
            {
                "title": "Portable ECG Biosignal Monitor & Wireless Data Acquisition",
                "description": "Develop a wearable biomedical signal processing device using instrumentation amplifiers, active bandpass filters, and MATLAB/Python digital filtering algorithms.",
                "suggested_stack": ["MATLAB", "LabVIEW", "Proteus", "Instrumentation Amplifiers", "Python"],
                "difficulty": "Advanced",
                "estimated_hours": 25,
                "market_relevance": "Directly aligns with Medical Device R&D live job postings for biosensor integration and clinical compliance.",
                "architecture_pipeline": [
                    {
                        "phase": "Phase 1: Analog Front-End Design",
                        "tasks": ["Design instrumentation amplifier stage", "Implement active Butterworth noise filter"]
                    },
                    {
                        "phase": "Phase 2: Digital Signal Processing",
                        "tasks": ["Write QRS complex detection algorithm in MATLAB", "Filter 60Hz powerline interference"]
                    },
                    {
                        "phase": "Phase 3: GUI & Data Logging",
                        "tasks": ["Build LabVIEW real-time waveform display", "Export heart rate variability metrics"]
                    }
                ],
                "key_features": ["High CMRR analog filtering", "Real-time QRS peak detection", "LabVIEW clinical interface"],
                "repository_structure": ["circuit/ecg_frontend.pdf", "dsp/qrs_detector.m", "gui/clinical_monitor.vi"]
            }
        ]
    elif "civil" in combined:
        return [
            {
                "title": "Multi-Story Earthquake-Resistant Building Structure",
                "description": "Perform structural frame analysis and seismic load modeling for a multi-story reinforced concrete building using STAAD.Pro and Revit BIM coordination.",
                "suggested_stack": ["STAAD.Pro", "Revit BIM", "AutoCAD", "ETABS", "MS Excel"],
                "difficulty": "Advanced",
                "estimated_hours": 28,
                "market_relevance": "Demonstrates structural engineering competency currently demanded in active civil engineering job ads.",
                "architecture_pipeline": [
                    {
                        "phase": "Phase 1: Structural Grid & Load Modeling",
                        "tasks": ["Draft structural grid in AutoCAD", "Define dead, live, and wind load vectors"]
                    },
                    {
                        "phase": "Phase 2: Seismic Analysis",
                        "tasks": ["Run dynamic response spectrum in STAAD.Pro", "Check story drift and column shear capacity"]
                    },
                    {
                        "phase": "Phase 3: BIM 3D Coordination",
                        "tasks": ["Generate Revit 3D structural model", "Produce rebar detailing drawings"]
                    }
                ],
                "key_features": ["Dynamic seismic response analysis", "ASCE 7 structural code compliance", "Revit BIM 3D model integration"],
                "repository_structure": ["models/building_frame.std", "bim/structural_model.rvt", "reports/seismic_calculation.pdf"]
            }
        ]

    # Default Electrical / System Project
    return [
        {
            "title": "High-Efficiency Switched-Mode Power Supply (SMPS) & Microcontroller Unit",
            "description": "Design a high-efficiency DC-DC buck converter circuit with Altium Designer PCB layout, closed-loop PWM voltage regulation, and LTspice simulation.",
            "suggested_stack": ["Altium Designer", "LTspice", "STM32 / C++", "MATLAB", "Proteus"],
            "difficulty": "Advanced",
            "estimated_hours": 28,
            "market_relevance": f"Highly valued in active job ads for {target_roles[0] if target_roles else 'Electrical Engineering'} positions requiring PCB layout and power conversion.",
            "architecture_pipeline": [
                {
                    "phase": "Phase 1: Circuit Topology & Simulation",
                    "tasks": ["Simulate Buck/Boost PWM switching in LTspice", "Calculate inductor and output capacitor values"]
                },
                {
                    "phase": "Phase 2: PCB Schematic & Layout",
                    "tasks": ["Create Altium schematic and component library", "Route 2-layer PCB with ground plane shielding"]
                },
                {
                    "phase": "Phase 3: Microcontroller Control Loop",
                    "tasks": ["Program STM32 ADC feedback sampling", "Implement digital PID PWM control in C/C++"]
                }
            ],
            "key_features": [">92% efficiency power conversion", "Altium 2-layer PCB layout", "Microcontroller closed-loop PWM regulation"],
            "repository_structure": ["hardware/power_supply.PcbDoc", "simulation/buck_converter.asc", "firmware/pid_pwm.c"]
        }
    ]


async def fetch_live_job_market_insights(target_roles: list[str]) -> list[str]:
    """Queries active job search APIs for the candidate's target roles
    to extract live job posting requirements, demanded skills, and tools."""
    if not target_roles:
        return []

    search_query = target_roles[0]
    market_snippets: list[str] = []

    try:
        try:
            from adapters.adzuna import search_adzuna
            from adapters.remotive import search_remotive
            from adapters.remoteok import search_remoteok
            from adapters.arbeitnow import search_arbeitnow
        except ImportError:
            from backend.adapters.adzuna import search_adzuna
            from backend.adapters.remotive import search_remotive
            from backend.adapters.remoteok import search_remoteok
            from backend.adapters.arbeitnow import search_arbeitnow

        adzuna_task = asyncio.create_task(search_adzuna(query=search_query, country="us", page=1))
        remotive_task = asyncio.create_task(search_remotive(query=search_query, page=1))
        remoteok_task = asyncio.create_task(search_remoteok(query=search_query, page=1))
        arbeitnow_task = asyncio.create_task(search_arbeitnow(query=search_query, page=1))

        results = await asyncio.gather(
            adzuna_task, remotive_task, remoteok_task, arbeitnow_task, return_exceptions=True
        )

        all_live_jobs = []
        for r in results:
            if isinstance(r, list):
                all_live_jobs.extend(r)

        for job in all_live_jobs[:10]:
            title = job.get("title", "")
            company = job.get("company", "")
            desc = job.get("description", "")[:180]
            if title:
                snippet = f"Live Active Job Posting: '{title}' at {company}. Description: {desc}"
                market_snippets.append(snippet)

    except Exception as e:
        logger.warning(f"Could not fetch live job market insights: {e}")

    return market_snippets[:6]


async def fetch_market_node(state: IdeaGeneratorState) -> dict:
    target_roles = state.get("target_roles", [])
    insights = await fetch_live_job_market_insights(target_roles)
    return {"live_market_insights": insights}


async def identify_skill_gaps(state: IdeaGeneratorState) -> dict:
    highest_edu = state.get("highest_education", "Engineering Degree")
    skills = state.get("skills", [])
    target_roles = state.get("target_roles", [])
    market_insights = state.get("live_market_insights", [])

    prompt = f"""You are a senior engineering career mentor analyzing active job market trends.

Candidate Profile from CV:
- Highest Education: {highest_edu}
- Current Skills: {", ".join(skills) if skills else "General Engineering"}
- Target Roles: {", ".join(target_roles) if target_roles else "Engineer"}

LIVE ACTIVE JOB MARKET ADS (Extracted from Job Sites for Candidate's Target Roles):
{json.dumps(market_insights, indent=2) if market_insights else "Active postings for target engineering roles."}

CRITICAL REQUIREMENT:
Analyze both the candidate's CV and the LIVE JOB MARKET ADS above.
Identify 3 to 5 REAL SKILL GAPS representing what active employers in today's job market are currently asking for in job postings that the candidate does NOT already have on their CV.

Return ONLY a valid JSON object matching this schema:
{{
  "skill_gaps": ["New Skill Gap 1", "New Skill Gap 2", "New Skill Gap 3"]
}}
"""

    try:
        raw_resp = await query_ollama(
            prompt=prompt,
            system_prompt="You are a senior technical career mentor.",
            temperature=0.2,
            json_format=True,
        )
        if not raw_resp:
            return {"skill_gaps": _get_domain_gaps(highest_edu, skills, target_roles)}

        json_str = clean_json_string(raw_resp)
        parsed = json.loads(json_str)
        gaps = parsed.get("skill_gaps", [])
        return {"skill_gaps": gaps if gaps else _get_domain_gaps(highest_edu, skills, target_roles)}
    except Exception as e:
        logger.error(f"Error in identify_skill_gaps node: {e}")
        return {"skill_gaps": _get_domain_gaps(highest_edu, skills, target_roles)}


async def generate_project_ideas(state: IdeaGeneratorState) -> dict:
    highest_edu = state.get("highest_education", "Engineering Degree")
    skills = state.get("skills", [])
    target_roles = state.get("target_roles", [])
    skill_gaps = state.get("skill_gaps", [])
    market_insights = state.get("live_market_insights", [])

    prompt = f"""You are a principal engineering architect designing market-driven portfolio projects.

Candidate Profile from CV:
- Highest Education: {highest_edu}
- Current Skills: {", ".join(skills)}
- Target Market Roles: {", ".join(target_roles)}
- Identified Skill Gaps to Bridge: {", ".join(skill_gaps)}

LIVE ACTIVE JOB MARKET ADS (Extracted from Job Sites for Candidate's Target Roles):
{json.dumps(market_insights, indent=2) if market_insights else "Active postings for target engineering roles."}

CRITICAL REQUIREMENTS:
1. Every project MUST directly correspond to candidate's discipline ({highest_edu}, {", ".join(target_roles[:2])}) and build real-world systems requested in active job market ads.
2. The projects MUST challenge the candidate to master their identified skill gaps ({", ".join(skill_gaps[:3])}).
3. Include a 4-phase step-by-step architecture pipeline, key features list, and folder structure.

Return ONLY a valid JSON object matching this schema:
{{
  "project_ideas": [
    {{
      "title": "Market-Driven Project Title",
      "description": "Clear 2-sentence description solving a real problem requested in active job ads.",
      "suggested_stack": ["Tool/Software 1", "Tool/Software 2", "Hardware/Framework 3"],
      "difficulty": "Advanced",
      "estimated_hours": 28,
      "market_relevance": "Direct reference to active job posting requirements for {target_roles[0] if target_roles else 'Engineers'}.",
      "architecture_pipeline": [
        {{
          "phase": "Phase 1: Design & Simulation",
          "tasks": ["Task 1", "Task 2"]
        }},
        {{
          "phase": "Phase 2: Core Engineering & Assembly",
          "tasks": ["Task 1", "Task 2"]
        }},
        {{
          "phase": "Phase 3: Integration & Control",
          "tasks": ["Task 1", "Task 2"]
        }},
        {{
          "phase": "Phase 4: Validation & Testing",
          "tasks": ["Task 1", "Task 2"]
        }}
      ],
      "key_features": ["Feature 1", "Feature 2", "Feature 3"],
      "repository_structure": ["cad/model.sldasm", "simulation/fem.ansys", "firmware/main.c"]
    }}
  ]
}}
"""

    try:
        raw_resp = await query_ollama(
            prompt=prompt,
            system_prompt="You are a principal engineering architect.",
            temperature=0.2,
            json_format=True,
            timeout=120.0,
        )
        if not raw_resp:
            return {"project_ideas": _get_domain_project_fallback(highest_edu, skills, target_roles)}

        json_str = clean_json_string(raw_resp)
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
                        {"phase": "Phase 1: Setup & Design", "tasks": ["Initialize design schematic", "Run preliminary simulation"]},
                        {"phase": "Phase 2: Core Assembly", "tasks": ["Build physical/digital model", "Integrate core components"]},
                        {"phase": "Phase 3: Validation", "tasks": ["Test load tolerances", "Optimize performance metrics"]}
                    ]

                validated_ideas.append({
                    "title": str(idea.get("title", "Engineering Project")),
                    "description": str(idea.get("description", "Practical engineering portfolio project.")),
                    "suggested_stack": [str(s) for s in idea.get("suggested_stack", ["MATLAB", "SolidWorks"])],
                    "difficulty": str(idea.get("difficulty", "Advanced")),
                    "estimated_hours": int(idea.get("estimated_hours", 25)),
                    "market_relevance": str(idea.get("market_relevance", "Directly requested in active job market postings.")),
                    "architecture_pipeline": pipeline,
                    "key_features": [str(f) for f in idea.get("key_features", ["High performance", "Industry compliance"])],
                    "repository_structure": [str(r) for r in idea.get("repository_structure", ["design/schematic.pdf", "simulation/test.m"])],
                })

        return {"project_ideas": validated_ideas[:6] if validated_ideas else _get_domain_project_fallback(highest_edu, skills, target_roles)}

    except Exception as e:
        logger.error(f"Error in generate_project_ideas node: {e}")
        return {"project_ideas": _get_domain_project_fallback(highest_edu, skills, target_roles)}


# Construct LangGraph workflow graph with Live Market Node
workflow = StateGraph(IdeaGeneratorState)

workflow.add_node("fetch_market_node", fetch_market_node)
workflow.add_node("identify_skill_gaps", identify_skill_gaps)
workflow.add_node("generate_project_ideas", generate_project_ideas)

workflow.set_entry_point("fetch_market_node")
workflow.add_edge("fetch_market_node", "identify_skill_gaps")
workflow.add_edge("identify_skill_gaps", "generate_project_ideas")
workflow.add_edge("generate_project_ideas", END)

idea_generator_graph = workflow.compile()


async def generate_ideas_agent(
    skills: list[str],
    target_roles: list[str],
    file_reference_id: str | None = None,
    highest_education: str = "Engineering Degree",
) -> dict:
    initial_state: IdeaGeneratorState = {
        "highest_education": highest_education,
        "skills": skills,
        "target_roles": target_roles,
        "file_reference_id": file_reference_id,
    }

    final_state = await idea_generator_graph.ainvoke(initial_state)

    return {
        "file_reference_id": file_reference_id,
        "highest_education": highest_education,
        "skills": skills,
        "target_roles": target_roles,
        "live_market_insights": final_state.get("live_market_insights", []),
        "skill_gaps": final_state.get("skill_gaps", []),
        "project_ideas": final_state.get("project_ideas", []),
    }
