# 🚀 Trajectory — Project Info & Comprehensive User Guide

> **AI-Powered Career Intelligence, Resume Auditing, Market Job Matcher & Portfolio Idea Generator**  
> *Driven by Local Ollama Qwen2.5 3B LLM, Vector Search, and Multi-Source Job Engines.*

---

## 📋 Table of Contents
1. [Project Overview](#-project-overview)
2. [Key Features & Core Architecture](#-key-features--core-architecture)
3. [How to Use This Project (Step-by-Step Guide)](#-how-to-use-this-project-step-by-step-guide)
4. [System Requirements & Installation](#-system-requirements--installation)
5. [Local Ollama AI Engine Setup](#-local-ollama-ai-engine-setup)
6. [API Endpoints Reference](#-api-endpoints-reference)
7. [Database & Security Schema](#-database--security-schema)

---

## 🌟 Project Overview

**Trajectory** is a modern, full-stack AI career platform designed to help job seekers, engineers, and developers land their ideal roles. Unlike generic job boards, Trajectory parses your resume, analyzes your full work experience, matches you against live job market openings with real job descriptions, identifies your actual skill gaps, and generates step-by-step portfolio project blueprints to help you bridge those gaps.

Everything in Trajectory runs **100% locally on your machine using Ollama and Qwen2.5 3B**, ensuring **zero API costs**, zero rate-limit quota issues, and **complete data privacy** for your resume files.

---

## ⚡ Key Features & Core Architecture

| Feature Component | Technology Used | Highlights |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js 16 (App Router), TailwindCSS, TypeScript | Modern glassmorphism UI, tabbed dashboard, interactive modals. |
| **Backend Service** | FastAPI (Python 3.11+), HTTPX, Pydantic | High-performance async microservice with CORS & custom adapters. |
| **Local AI Engine** | Ollama REST API (`qwen2.5:3b`) | Zero API keys required; robust JSON parsing for structured responses. |
| **Job Market Search** | Adzuna, Remotive, RemoteOK, Arbeitnow, Jooble | Concurrent multi-adapter search engine with country & remote filters. |
| **Vector Engine** | `sentence-transformers` (`all-MiniLM-L6-v2`) | 384-dimensional dense semantic vectors for profile-to-job matching. |
| **Authentication & DB** | Supabase Auth, PostgreSQL, `pgvector` | Instant email sign-in, profile synchronization, and strict RLS policies. |

---

## 🧭 How to Use This Project (Step-by-Step Guide)

### Step 1: Account Access & Instant Sign-In
1. Launch the application in your web browser at **`http://localhost:3000`**.
2. If you are not signed in, you will be automatically redirected to **`http://localhost:3000/login`**.
3. **Existing Users**: Enter your registered email address under the **"Sign In"** tab and click **"Enter Dashboard Instantly"**. You will enter your dashboard immediately without needing a confirmation code.
4. **New Users**: Click the **"Create Account"** tab, enter your Full Name and Email Address, then click **"Create Account & Send Code"**. Check your inbox for the 6-digit confirmation code, enter it, and click **"Verify & Complete Registration"**.

---

### Step 2: Uploading & Auditing Your Resume (CV Audit)
1. Go to the **Resume Analyzer** dashboard (`http://localhost:3000/dashboard`).
2. Click on the **"My CV & Audit"** tab.
3. Click **"Choose File"** to select your resume in **PDF** or **DOCX** format.
4. Click **"Upload & Analyze CV"**.
5. Trajectory will extract your text and process it through the local **Ollama Qwen2.5 3B AI agent**. You will receive:
   - **Highest Education Degree** (e.g., *Bachelor of Science in Mechanical Engineering*).
   - **Seniority Level Badge** (e.g., *Mid-Level*, *Senior*).
   - **Executive Summary Pitch** summarizing your actual field, degree, and career background.
   - **Key Technical Strengths** & **Resume Improvement Recommendations**.

---

### Step 3: Viewing AI-Matched Jobs with Real Job Descriptions
1. Click on the **"Matched Jobs"** tab on the dashboard.
2. Trajectory automatically searches live market engines (Adzuna, Remotive, RemoteOK, Arbeitnow, Jooble) using your target engineering/developer role.
3. Each job listing includes:
   - **Job Title & Company Name**.
   - **Location & Remote Badge**.
   - **Source Site Job Description Snippet** (2–3 sentences explaining the actual responsibilities from the hiring site).
   - **Natural Language AI Match Reasoning** generated specifically for your profile background (e.g., *"Directly aligns with your Biomedical Engineering degree and MATLAB expertise."*).

---

### Step 4: Skill Gap Analysis & Portfolio Project Generation
1. Click on the **"Portfolio Ideas"** tab on the dashboard.
2. Trajectory compares your extracted CV skills against active market job postings to identify **Genuine Skill Gaps** (e.g., *PLC Programming, ROS2, Docker, Scikit-Learn*).
3. Browse generated **Market-Influenced Portfolio Project Ideas** tailored to bridge your exact skill gaps.
4. Click **"Start Project &rarr;"** on any project card to open the **Interactive Technical Blueprint Modal**:
   - **System Architecture & Data Flow**: 4-phase step-by-step execution roadmap.
   - **Key Features & Tech Stack**: Languages, frameworks, and tools to use.
   - **Repository Folder Structure**: Exact file tree layout for your GitHub repository.

---

### Step 5: Searching Jobs & Borderless Freelance Mode
1. Click **"Job Search"** in the top navigation bar (`http://localhost:3000`).
2. Enter any job query (e.g., *Electrical Engineer*, *Data Scientist*, *React Developer*).
3. Filter by **Country** (US, UK, Germany, Canada, Pakistan, etc.), **City**, or **Work Mode** (Remote, Onsite, Hybrid).
4. **Freelance / Gig Mode**: Toggle the **"Freelance / Gig Jobs Only"** switch to search borderless gig contracts and access direct deep-links to **Upwork**, **Fiverr**, **Freelancer**, **Toptal**, and **Rozee.pk**.

---

### Step 6: Account Deletion
1. To permanently delete your account and all stored data, click the **"Delete Account"** button in the header bar.
2. Confirm deletion in the modal dialog. Trajectory will delete your user profile, stored resume files, search history, and Supabase auth record, returning you to the login screen.

---

## ⚙️ System Requirements & Installation

### Prerequisites
- **Node.js**: v18.0 or higher
- **Python**: 3.11 or higher
- **Ollama**: Installed locally on your computer ([Download Ollama](https://ollama.com))

---

### 1. Install & Run Local Ollama Model
```bash
# Pull and start Qwen2.5 3B model locally
ollama pull qwen2.5:3b
```

---

### 2. Set Up FastAPI Backend
```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install backend dependencies
pip install -r requirements.txt

# Start backend dev server on port 8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

### 3. Set Up Next.js Frontend
```bash
cd frontend

# Install frontend dependencies
npm install

# Start Next.js dev server on port 3000
npm run dev
```

Open `http://localhost:3000` in your web browser.

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server health check endpoint. |
| `GET` | `/jobs/search` | Search jobs across 5 live job engines with filters. |
| `POST` | `/resume/upload` | Upload PDF/DOCX file and extract plain text. |
| `POST` | `/resume/analyze` | Run local Ollama Qwen2.5 3B agent CV audit. |
| `GET` | `/jobs/matched` | Match candidate vector against live job listings. |
| `POST` | `/ideas/generate` | Generate skill gaps and 4-phase project architecture blueprints. |
| `POST` | `/user/profile/sync` | Sync user profile data to database. |
| `POST` | `/user/profile/lookup` | Check if user email is registered. |
| `DELETE` | `/user/account` | Permanently delete user account and stored data. |

---

## 🔒 Database & Security Schema

Trajectory uses PostgreSQL with Supabase Row-Level Security (RLS):
- **`public.profiles`**: Stores `id` (UUID), `email`, `full_name`, and `cv_summary`.
- **`public.resumes`**: Stores uploaded file metadata, extracted text, skills, and tools.
- **`public.profile_embeddings`**: Stores `vector(384)` embeddings with HNSW indexes for similarity search.
- **`public.saved_searches`**: Stores user search preferences and history.
