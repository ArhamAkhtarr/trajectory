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
    highest_education: str
    skills: list[str]
    target_roles: list[str]
    file_reference_id: str | None
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


def _clean_json_str(text: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text.strip()


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
                "market_relevance": f"In-demand for Mechanical Engineering roles to demonstrate structural load simulation, CAD assembly, and mechatronic control.",
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
                "market_relevance": "Directly aligns with Medical Device R&D demands for biosensor integration and clinical compliance.",
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
                "market_relevance": "Demonstrates structural engineering competency in seismic design codes and 3D BIM coordination.",
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
            "market_relevance": f"Highly valued in {target_roles[0] if target_roles else 'Electrical Engineering'} positions requiring hardware PCB design and power conversion efficiency.",
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


async def identify_skill_gaps(state: IdeaGeneratorState) -> dict:
    highest_edu = state.get("highest_education", "Engineering Degree")
    skills = state.get("skills", [])
    target_roles = state.get("target_roles", [])
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing. Using domain gap fallbacks.")
        return {"skill_gaps": _get_domain_gaps(highest_edu, skills, target_roles)}

    prompt = f"""You are a senior engineering career mentor. Identify 3 to 5 CRITICAL SKILL GAPS for a candidate to elevate their portfolio for high-growth industry roles.

Candidate Profile:
- Highest Education: {highest_edu}
- Current Skills: {", ".join(skills) if skills else "General Engineering"}
- Target Roles: {", ".join(target_roles) if target_roles else "Engineer"}

CRITICAL REQUIREMENT:
Do NOT simply repeat the candidate's existing skills back to them.
Identify NEW, high-demand industry skills, tools, software, or standards (e.g. for Mechanical: CFD Simulation, Additive Manufacturing, GD&T; for Electrical: RTOS, High-Speed PCB Layout, CAN Bus, FPGA; for Biomedical: ISO 14971, FDA 510(k), Biosensors) that the candidate currently lacks and MUST master to get hired in {", ".join(target_roles[:2])}.

Return ONLY a valid JSON object matching this schema:
{{
  "skill_gaps": ["New Skill Gap 1", "New Skill Gap 2", "New Skill Gap 3"]
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
        return {"skill_gaps": gaps if gaps else _get_domain_gaps(highest_edu, skills, target_roles)}
    except Exception as e:
        logger.error(f"Error in identify_skill_gaps node: {e}")
        return {"skill_gaps": _get_domain_gaps(highest_edu, skills, target_roles)}


async def generate_project_ideas(state: IdeaGeneratorState) -> dict:
    highest_edu = state.get("highest_education", "Engineering Degree")
    skills = state.get("skills", [])
    target_roles = state.get("target_roles", [])
    skill_gaps = state.get("skill_gaps", [])
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing. Using fallback project ideas.")
        return {"project_ideas": _get_domain_project_fallback(highest_edu, skills, target_roles)}

    prompt = f"""You are a principal engineering architect. Generate 4 to 6 FRESH, INNOVATIVE portfolio project recommendations.

Candidate Profile:
- Highest Education: {highest_edu}
- Current Skills: {", ".join(skills)}
- Target Market Roles: {", ".join(target_roles)}
- Identified Skill Gaps to Bridge: {", ".join(skill_gaps)}

CRITICAL REQUIREMENTS:
1. Every project MUST directly correspond to candidate's EXACT discipline ({highest_edu}, {", ".join(target_roles[:2])}).
   - If Electrical Engineering: PCB design, microcontrollers, LTspice, signal processing, power electronics.
   - If Mechanical Engineering: 3D CAD modeling (SolidWorks/CATIA), FEA stress analysis (Ansys), thermal fluid simulation, robotics.
   - If Biomedical Engineering: Medical device prototyping, biosignal processing (MATLAB/LabVIEW), biomaterials, FDA compliance.
   - If Civil Engineering: Structural analysis (STAAD.Pro/ETABS), Revit 3D BIM modeling, geotechnical simulation.
   - If Chemical Engineering: Process simulation (Aspen HYSYS), reaction kinetics, plant safety.
2. The projects MUST challenge the candidate to bridge their identified skill gaps ({", ".join(skill_gaps[:3])}) and build real-world engineering artifacts.
3. Include a 4-phase step-by-step architecture pipeline, key features list, and folder structure.

Return ONLY a valid JSON object matching this schema:
{{
  "project_ideas": [
    {{
      "title": "Innovative Project Title",
      "description": "Clear 2-sentence description combining candidate's background with new target skills.",
      "suggested_stack": ["Tool/Software 1", "Tool/Software 2", "Hardware/Framework 3"],
      "difficulty": "Advanced",
      "estimated_hours": 28,
      "market_relevance": "Why hiring managers for {target_roles[0] if target_roles else 'Engineers'} value this project.",
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
                    "market_relevance": str(idea.get("market_relevance", "High market demand for target engineering roles.")),
                    "architecture_pipeline": pipeline,
                    "key_features": [str(f) for f in idea.get("key_features", ["High performance", "Industry compliance"])],
                    "repository_structure": [str(r) for r in idea.get("repository_structure", ["design/schematic.pdf", "simulation/test.m"])],
                })

        return {"project_ideas": validated_ideas[:6]}

    except Exception as e:
        logger.error(f"Error in generate_project_ideas node: {e}")
        return {"project_ideas": _get_domain_project_fallback(highest_edu, skills, target_roles)}


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
        "skill_gaps": final_state.get("skill_gaps", []),
        "project_ideas": final_state.get("project_ideas", []),
    }
