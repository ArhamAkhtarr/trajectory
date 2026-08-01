# 🚀 Trajectory — AI Career Intelligence & Job Matching Platform

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 16](https://img.shields.io/badge/Next.js-16_Turbopack-000000.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![Ollama Qwen2.5 3B](https://img.shields.io/badge/Ollama-Qwen2.5_3B-FF6F00.svg?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)
[![Supabase pgvector](https://img.shields.io/badge/Supabase-pgvector-3ECF8E.svg?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Tests Passing](https://img.shields.io/badge/Pytest-37%2F37_Passed-brightgreen.svg?style=for-the-badge&logo=pytest&logoColor=white)](#-testing)

> **Trajectory** is a full-stack AI career intelligence platform. It analyzes resumes across multi-domain engineering and tech fields, searches live job boards concurrently, matches candidate profiles using vector embeddings, identifies skill gaps, and generates step-by-step portfolio project architecture blueprints.

---

## ✨ Features

- 📄 **Deep Resume Auditing**: Parses PDF and DOCX files. Automatically detects field domain (Mechanical, Electrical, Biomedical, Civil, Chemical, Data Science, Software), highest education degree, seniority level, and core strengths.
- 🤖 **100% Local AI Model (Ollama Qwen2.5 3B)**: Operates completely offline with zero API key dependencies or quota limits.
- 🔎 **Concurrent Multi-Source Job Engine**: Searches Adzuna, Remotive, RemoteOK, Arbeitnow, and Jooble simultaneously with strict query token matching, country mapping, and work mode filters.
- 💼 **Gig & Freelance Mode**: Surfaces borderless freelance opportunities with direct deep-links to Upwork, Fiverr, Freelancer, Toptal, and Rozee.pk.
- 📐 **Vector Embeddings & Semantic Matching**: Uses `sentence-transformers` (`all-MiniLM-L6-v2`) to compute 384-dimensional profile vectors, re-ranking candidate jobs with natural language match reasoning.
- 💡 **Market-Driven Portfolio Idea Generator**: Identifies genuine missing competencies from active job listings and constructs 4-phase technical project blueprints with repository folder structures.
- 🔐 **Authentication & Security**: Email confirmation code OTP verification, instant sign-in for registered users, and PostgreSQL Row Level Security (RLS) on Supabase.
- 🗑️ **Account Deletion**: Self-service account deletion purging user profiles, resumes, search history, and Supabase auth records.

---

## 🏗️ Repository Structure

```
trajectory/
├── 📁 backend/                        # FastAPI Microservice & AI Agents
│   ├── 📄 main.py                      # REST endpoints & API controllers
│   ├── 📄 requirements.txt             # Python package dependencies
│   ├── 📄 supabase_schema.sql          # PostgreSQL table schema & RLS policies
│   ├── 📁 agents/                      # LangGraph AI agents (Resume & Idea Generator)
│   ├── 📁 services/                    # Ollama client, vector matcher, document parser
│   ├── 📁 adapters/                    # Multi-board job scrapers (Adzuna, Remotive, etc.)
│   └── 📁 tests/                       # Complete 37-test Pytest suite
├── 📁 frontend/                       # Next.js 16 App Router UI
│   ├── 📁 app/                         # App Router pages (Search, Login, Dashboard)
│   └── 📁 lib/                         # Supabase web client & country lists
├── 📄 project_info.md                  # Comprehensive User Guide & Setup Guide
├── 📄 project_pipeline.md              # Visual System Architecture & Execution Pipeline
├── 📄 concepts.md                      # AI & Technical Concept Guide (Basic to Advanced)
└── 📄 README.md                        # Master Repository Documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Node.js**: v18+
- **Python**: 3.11+
- **Ollama**: Installed locally ([ollama.com](https://ollama.com))

---

### 2. Start Local Ollama AI Model
```bash
ollama pull qwen2.5:3b
```

---

### 3. Setup Backend (FastAPI)
```bash
cd backend

# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start backend server on port 8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend Health Check: `http://localhost:8000/health`

---

### 4. Setup Frontend (Next.js 16)
```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server on port 3000
npm run dev
```
Open `http://localhost:3000` in your web browser.

---

## 📡 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | API Health status check. |
| `/jobs/search` | `GET` | Multi-adapter concurrent job search with country and remote filters. |
| `/resume/upload` | `POST` | Upload resume file (`PDF`/`DOCX`) and extract plain text. |
| `/resume/analyze` | `POST` | Analyze resume with local Ollama Qwen2.5 3B AI agent. |
| `/jobs/matched` | `GET` | Compute vector similarity match against candidate resume profile. |
| `/ideas/generate` | `POST` | Detect skill gaps and generate 4-phase project architecture blueprints. |
| `/user/profile/sync` | `POST` | Sync user profile data into PostgreSQL database. |
| `/user/profile/lookup` | `POST` | Check if user email is registered. |
| `/user/account` | `DELETE` | Permanently delete user account and stored data. |

---

## 🧪 Testing

Run the automated pytest suite (37 tests):

```bash
cd backend
.venv/bin/python -m pytest tests/
```

```
======================== 37 passed in 5.77s ========================
```

---

## 📚 Detailed Documentation

- 📖 **[project_info.md](file:///Users/m1pro/Projects/trajectory/project_info.md)** &mdash; Full User Guide & How-to Step-by-Step Instructions.
- 🎨 **[project_pipeline.md](file:///Users/m1pro/Projects/trajectory/project_pipeline.md)** &mdash; Visual System Architecture & Data Flow Diagram.
- 💡 **[concepts.md](file:///Users/m1pro/Projects/trajectory/concepts.md)** &mdash; Comprehensive AI & Engineering Concepts (Basic to Advanced).
