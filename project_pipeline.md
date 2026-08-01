# 🎨 Trajectory — Architecture & Technical Execution Pipeline

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 16](https://img.shields.io/badge/Next.js-16_Turbopack-000000.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![Ollama Qwen2.5 3B](https://img.shields.io/badge/Ollama-Qwen2.5_3B-FF6F00.svg?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)
[![Supabase pgvector](https://img.shields.io/badge/Supabase-pgvector-3ECF8E.svg?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Tests Passing](https://img.shields.io/badge/Pytest-37%2F37_Passed-brightgreen.svg?style=for-the-badge&logo=pytest&logoColor=white)](#-verification--test-suite)

> **Trajectory** orchestrates local AI model inference, sentence transformer vector embeddings, multi-adapter job market scrapers, and PostgreSQL database storage into a high-performance career intelligence platform.

---

## 📐 System Architecture Blueprint

```mermaid
flowchart TD
    %% Custom Styling
    classDef feStyle fill:#1e1b4b,stroke:#6366f1,stroke-width:2px,color:#fff;
    classDef beStyle fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef aiStyle fill:#78350f,stroke:#f59e0b,stroke-width:2px,color:#fff;
    classDef dbStyle fill:#312e81,stroke:#818cf8,stroke-width:2px,color:#fff;

    subgraph FE ["🌐 FRONTEND LAYER (Next.js 16 Turbopack)"]
        UI_Search["🔍 Search Portal<br/>(app/page.tsx)"]:::feStyle
        UI_Auth["🔑 Auth Page<br/>(app/login/page.tsx)"]:::feStyle
        UI_Dash["📊 Dashboard<br/>(app/dashboard/page.tsx)"]:::feStyle
    end

    subgraph BE ["⚡ BACKEND API LAYER (FastAPI Microservice)"]
        API["⚙️ FastAPI Controller<br/>(main.py)"]:::beStyle
        
        subgraph AGENTS ["🤖 LOCAL AI AGENTS"]
            Agent_Resume["📄 Resume Analyzer<br/>(agents/resume_analyzer.py)"]:::aiStyle
            Agent_Idea["💡 Idea Generator<br/>(agents/idea_generator.py)"]:::aiStyle
        end
        
        subgraph ENGINE ["🔎 SEARCH ADAPTER ENGINE"]
            Adzuna["Adzuna Adapter"]:::beStyle
            Remotive["Remotive Adapter"]:::beStyle
            RemoteOK["RemoteOK Adapter"]:::beStyle
            Arbeitnow["Arbeitnow Adapter"]:::beStyle
            Jooble["Jooble Adapter"]:::beStyle
        end

        subgraph VECTOR ["📐 VECTOR ENGINE"]
            Embedder["Sentence-Transformers<br/>(all-MiniLM-L6-v2)"]:::beStyle
            Matcher["Cosine Similarity<br/>(matching_service.py)"]:::beStyle
        end
    end

    subgraph OLLAMA ["🧠 LOCAL LLM INFERENCE ENGINE"]
        OllamaModel["🦙 Ollama REST API<br/>Model: qwen2.5:3b"]:::aiStyle
    end

    subgraph DATA ["🗄️ PERSISTENCE LAYER (Supabase)"]
        SupaDB[("PostgreSQL + pgvector<br/>(supabase_schema.sql)")]:::dbStyle
    end

    UI_Search -->|Search Query| API
    UI_Dash -->|Upload CV File| API
    API --> Agent_Resume
    API --> Agent_Idea
    API --> ENGINE
    Agent_Resume -->|Structured JSON Prompt| OllamaModel
    Agent_Idea -->|Market Gap Prompt| OllamaModel
    Agent_Resume -->|Compute Profile Vector| Embedder
    Embedder -->|Store Vector| SupaDB
    ENGINE --> Matcher
    Matcher -->|Re-rank Match Reasoning| OllamaModel
    API -->|Save Profile & Resumes| SupaDB
```

---

## 🗺️ File-by-File Component Index

```
trajectory/
├── 📁 backend/
│   ├── 📄 main.py                      # FastAPI REST controllers & API routes
│   ├── 📄 requirements.txt             # Python dependencies
│   ├── 📁 agents/
│   │   ├── 📄 resume_analyzer.py       # Local Ollama CV parser & multi-domain audit agent
│   │   └── 📄 idea_generator.py        # Skill gap identifier & 4-phase project builder agent
│   ├── 📁 services/
│   │   ├── 📄 ollama_service.py        # Local Ollama REST client & JSON code-block parser
│   │   ├── 📄 matching_service.py      # Sentence-Transformer vector matcher & LLM re-ranker
│   │   └── 📄 resume_service.py        # PDF/DOCX document text extraction & Supabase storage
│   ├── 📁 adapters/
│   │   ├── 📄 adzuna.py                # Adzuna job market API adapter
│   │   ├── 📄 remotive.py              # Remotive remote jobs API adapter
│   │   ├── 📄 remoteok.py              # RemoteOK jobs API adapter
│   │   ├── 📄 arbeitnow.py             # Arbeitnow jobs API adapter
│   │   ├── 📄 jooble.py                # Jooble job search API adapter
│   │   └── 📄 utils.py                 # Query relevance, country filter, & dedup logic
│   └── 📁 tests/                       # Complete 37-test pytest suite
├── 📁 frontend/
│   ├── 📁 app/
│   │   ├── 📄 page.tsx                 # Search portal with Gig/Freelance mode & deep-links
│   │   ├── 📄 login.tsx                # Instant sign-in & email confirmation code OTP flow
│   │   └── 📄 dashboard/page.tsx       # Matched Jobs, Portfolio Ideas, & CV Audit UI
│   └── 📁 lib/
│       └── 📄 supabaseClient.ts        # Supabase browser auth & database client
├── 📄 project_info.md                  # Comprehensive user guide & setup documentation
├── 📄 project_pipeline.md              # Visual system architecture & pipeline breakdown
├── 📄 concepts.md                      # Complete AI & technical concept guide (Basic to Advanced)
└── 📄 README.md                        # Master repository documentation
```

---

## 🔄 End-to-End Execution Flow

> [!NOTE]
> **Stage 1: Document Upload & Parsing**  
> User uploads a resume file (`PDF` or `DOCX`). `services/resume_service.py` extracts raw text content using `pdfplumber` or `python-docx`.

> [!TIP]
> **Stage 2: Local AI Resume Audit**  
> `agents/resume_analyzer.py` sends the raw resume text to `services/ollama_service.py`, querying local model **`qwen2.5:3b`**. It extracts highest education, seniority, skills, tools, and a candidate pitch without cloud API fees.

> [!IMPORTANT]
> **Stage 3: Dense Vector Embedding & Matching**  
> `services/matching_service.py` encodes the candidate profile using `all-MiniLM-L6-v2` into a 384-dimensional vector. It computes Cosine Similarity against live job descriptions, re-ranking the top matches with local Ollama match reasoning.

> [!TIP]
> **Stage 4: Market-Driven Project Blueprinting**  
> `agents/idea_generator.py` queries live job search adapters for active candidate roles, identifies genuine missing skills, and constructs a 4-phase technical project architecture blueprint.

---

## 🧪 Verification & Test Suite

The backend contains a 37-test automated test suite covering all services, agents, adapters, and search filters:

```bash
cd backend
.venv/bin/python -m pytest tests/
```

```
======================== 37 passed in 5.77s ========================
```
