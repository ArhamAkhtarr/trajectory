# 🧠 Trajectory — Core Technical & AI Concepts Guide

> **From Basic Principles to Advanced Implementation**  
> *A comprehensive engineering breakdown explaining every technical concept used in Trajectory, using Trajectory's codebase as the primary learning example.*

---

## 📋 Table of Contents
1. [Asynchronous Multi-Source Web Scraping & API Adapters](#1-asynchronous-multi-source-web-scraping--api-adapters)
2. [Document Parsing & Text Extraction (PDF & DOCX)](#2-document-parsing--text-extraction-pdf--docx)
3. [Local LLM Inference & Structured JSON Extraction (Ollama & Qwen2.5 3B)](#3-local-llm-inference--structured-json-extraction-ollama--qwen25-3b)
4. [Multi-Domain CV Analysis & Experience-Based Heuristics](#4-multi-domain-cv-analysis--experience-based-heuristics)
5. [Vector Embeddings & Dense Semantic Search](#5-vector-embeddings--dense-semantic-search)
6. [Market-Influenced Skill Gap Detection & Project Blueprinting](#6-market-influenced-skill-gap-detection--project-blueprinting)
7. [Authentication, Identity & Row Level Security (RLS)](#7-authentication-identity--row-level-security-rls)
8. [Microservices Architecture & Modern Web Stack](#8-microservices-architecture--modern-web-stack)

---

## 1. Asynchronous Multi-Source Web Scraping & API Adapters

### 🟢 Basic Concept
When you search for jobs on the internet, job postings are scattered across dozens of different websites (Adzuna, Remotive, RemoteOK, Jooble, etc.). Instead of opening 5 different websites manually, an **API Adapter** is a custom script that talks to each website's computer system (API), retrieves the job listings in raw data format, and brings them back into a single place.

### 🟡 Intermediate Concept
If you fetch 5 different websites one after another (synchronously), searching takes 15–20 seconds because your computer sits waiting for each website to respond before starting the next one.  
In **Asynchronous Programming (`async/await`)**, your computer sends requests to all 5 websites simultaneously without waiting. Python's `asyncio.gather()` fires all HTTP requests in parallel, reducing total wait time to the speed of the single slowest website (~1-2 seconds).

### 🔴 Advanced Implementation in Trajectory
In Trajectory's backend:
- **Adapters ([`backend/adapters/`](file:///Users/m1pro/Projects/trajectory/backend/adapters))**: Custom adapters (`adzuna.py`, `remotive.py`, `remoteok.py`, `arbeitnow.py`, `jooble.py`) map disparate JSON payloads into a standardized `Job` schema.
- **Concurrent Dispatch ([`backend/main.py`](file:///Users/m1pro/Projects/trajectory/backend/main.py#L96-L103))**:
  ```python
  raw_results = await asyncio.gather(
      _safe_search(search_adzuna, query, country, city, page),
      _safe_search(search_remotive, query, country, city, page),
      _safe_search(search_remoteok, query, country, city, page),
      _safe_search(search_arbeitnow, query, country, city, page),
      _safe_search(search_jooble, query, country, city, page),
      return_exceptions=True,
  )
  ```
- **Deduplication & Filtering ([`backend/adapters/utils.py`](file:///Users/m1pro/Projects/trajectory/backend/adapters/utils.py))**:
  - `deduplicate_jobs`: Uses normalized `(title, company)` keys to eliminate duplicate job postings aggregated across multiple boards.
  - `is_query_relevant`: Enforces token matching to discard unrelated job titles (e.g. discarding "Software Sales" when searching "Software Engineer").

---

## 2. Document Parsing & Text Extraction (PDF & DOCX)

### 🟢 Basic Concept
Resumes are saved as binary PDF files or Microsoft Word `.docx` documents. These files contain visual formatting, fonts, images, and layout blocks. Before an AI model can read a resume, software must extract the plain raw text inside the document.

### 🟡 Intermediate Concept
PDF documents do not store text as simple sentences; they store text as geometric visual coordinates on a two-dimensional grid (e.g., character 'A' at coordinates `x=120, y=450`). Text extraction libraries read these font streams and reconstruct natural sentence layouts, lines, and paragraphs.

### 🔴 Advanced Implementation in Trajectory
In Trajectory's document processing service ([`backend/services/resume_service.py`](file:///Users/m1pro/Projects/trajectory/backend/services/resume_service.py)):
- Uses **`pdfplumber`** for multi-column PDF layout reconstruction, falling back to **`PyPDF2`** if layout tables are simple.
- Uses **`python-docx`** to inspect paragraph XML elements in Word documents.
- Normalizes whitespace, removes control characters, and prepares raw text for LLM tokenization.

---

## 3. Local LLM Inference & Structured JSON Extraction (Ollama & Qwen2.5 3B)

### 🟢 Basic Concept
A Large Language Model (LLM) is an AI neural network trained on vast amounts of text. Instead of relying on expensive cloud API keys (such as Anthropic Claude or OpenAI GPT-4) which charge money per request and hit rate limits, **Ollama** lets you run state-of-the-art open-source models (like Alibaba's **Qwen2.5 3B**) directly on your personal computer.

### 🟡 Intermediate Concept
LLMs produce conversational natural language by default. However, web applications require structured data (JSON format with keys like `"skills"`, `"suggested_roles"`, `"highest_education"`). Getting an LLM to reliably return valid JSON without extra conversational text (e.g., *"Here is your JSON response..."*) requires structured prompting and markdown code-fence parsing.

### 🔴 Advanced Implementation in Trajectory
In Trajectory's Ollama service ([`backend/services/ollama_service.py`](file:///Users/m1pro/Projects/trajectory/backend/services/ollama_service.py)):
1. **Local REST API Dispatch**: Communicates with Ollama running locally at `http://localhost:11434/api/generate` using model `qwen2.5:3b`.
2. **Robust JSON Extraction (`clean_json_string`)**:
   ```python
   def clean_json_string(text: str) -> str:
       # Extracts clean JSON objects {...} or arrays [...] out of raw LLM markdown code blocks
       match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
       if match:
           return match.group(1).strip()
       # Fallback to direct string matching
       start_obj = text.find('{')
       end_obj = text.rfind('}')
       if start_obj != -1 and end_obj != -1:
           return text[start_obj:end_obj + 1]
       return text.strip()
   ```
3. Zero cloud API key dependency ensures 100% free, private, and offline execution.

---

## 4. Multi-Domain CV Analysis & Experience-Based Heuristics

### 🟢 Basic Concept
Simple resume scanners search for single keywords. If a resume mentions the word "Python", a basic scanner assumes the person is a Software Engineer. However, an Electrical Engineer might use Python for circuit simulation, or a Mechanical Engineer might use Python for CAD automation.

### 🟡 Intermediate Concept
To accurately identify a candidate's real career field, a system must analyze the **combination of degree education, tools used, and work experience history**.

### 🔴 Advanced Implementation in Trajectory
In Trajectory's Resume Analyzer ([`backend/agents/resume_analyzer.py`](file:///Users/m1pro/Projects/trajectory/backend/agents/resume_analyzer.py)):
- **Work Experience Priority**: Evaluates job title history, duties performed, and degree background (`highest_education`).
- **Dynamic Field Classification**: Classifies candidates into specialized engineering domains:
  - **Mechanical Engineering**: CAD, SolidWorks, Thermodynamics, Finite Element Analysis (FEA), HVAC.
  - **Electrical Engineering**: PCBs, Microcontrollers, Verilog, FPGA, MATLAB, Signal Processing.
  - **Biomedical Engineering**: Medical Devices, Biomechanics, Tissue Engineering, DICOM.
  - **Civil Engineering**: Structural Analysis, AutoCAD, Geotechnical, Surveying, Revit.
  - **Chemical Engineering**: Process Control, Reaction Kinetics, Mass Transfer, Aspen Plus.
  - **Data Science**: Machine Learning, PyTorch, Pandas, Scikit-Learn, SQL.
  - **Software Engineering**: React, Next.js, Node.js, Docker, Microservices.

---

## 5. Vector Embeddings & Dense Semantic Search

### 🟢 Basic Concept
Traditional search looks for exact keyword matches. If a candidate's resume says *"Expertise in Microcontrollers and Circuit Design"*, and a job posting asks for *"PCB Layout Engineer"*, exact keyword search will fail to match them because the exact words don't match.

### 🟡 Intermediate Concept
**Vector Embeddings** convert words, sentences, or candidate resumes into lists of floating-point numbers (vectors) in a multi-dimensional mathematical space. Sentences with similar meanings are positioned close together in vector space, even if they use completely different words.

### 🔴 Advanced Implementation in Trajectory
In Trajectory's Matching Service ([`backend/services/matching_service.py`](file:///Users/m1pro/Projects/trajectory/backend/services/matching_service.py)):
1. **Sentence-Transformers (`all-MiniLM-L6-v2`)**: Converts resume profiles and job descriptions into **384-dimensional dense vectors**.
2. **Cosine Similarity Computation**:
   \[
   \text{Cosine Similarity} = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}
   \]
3. **LLM Re-ranking**: The top vector matches are re-ranked using local Ollama Qwen2.5 3B to generate natural language candidate match reasoning.

---

## 6. Market-Influenced Skill Gap Detection & Project Blueprinting

### 🟢 Basic Concept
Job seekers often don't know what projects to build for their portfolio to impress recruiters. Building generic tutorial projects (like a basic To-Do list) does not showcase market readiness.

### 🟡 Intermediate Concept
By scraping live job postings in the candidate's target field right now, an AI system can extract the exact skills currently demanded by hiring managers and compare them against the candidate's existing resume skills to pinpoint missing competencies (**Skill Gaps**).

### 🔴 Advanced Implementation in Trajectory
In Trajectory's Idea Generator ([`backend/agents/idea_generator.py`](file:///Users/m1pro/Projects/trajectory/backend/agents/idea_generator.py)):
1. **Live Market Scraping (`fetch_market_node`)**: Fetches active job listings for the candidate's target roles.
2. **Skill Gap Identification**: Compares extracted resume skills against market requirements.
3. **4-Phase Architecture Blueprint Generation**: Produces step-by-step project specs containing:
   - System Architecture & Data Flow roadmap.
   - Core Features & Required Tech Stack.
   - Exact Repository Folder Structure (file tree layout).

---

## 7. Authentication, Identity & Row Level Security (RLS)

### 🟢 Basic Concept
User authentication verifies who a user is (Sign In / Sign Up), while authorization determines what data that user is allowed to view or modify in the database.

### 🟡 Intermediate Concept
**Email OTP (One-Time Password / Confirmation Code)** sends a temporary 6-digit verification code to a user's email address during sign-up to prove email ownership without requiring password management.

### 🔴 Advanced Implementation in Trajectory
In Trajectory's database and frontend ([`backend/supabase_schema.sql`](file:///Users/m1pro/Projects/trajectory/backend/supabase_schema.sql) & [`frontend/app/login/page.tsx`](file:///Users/m1pro/Projects/trajectory/frontend/app/login/page.tsx)):
- **Supabase Auth & OTP**: Email verification during account creation. Instant dashboard entry for registered users.
- **Row-Level Security (RLS)**:
  ```sql
  CREATE POLICY "Users can view own resumes"
      ON public.resumes FOR SELECT
      USING (auth.uid() = user_id);
  ```
  Ensures that PostgreSQL database rows can only be accessed by the user who owns them.

---

## 8. Microservices Architecture & Modern Web Stack

### 🟢 Basic Concept
A web application is divided into two parts: the **Frontend** (what the user sees in their browser) and the **Backend** (the server running logic, AI agents, and database operations).

### 🟡 Intermediate Concept
**Next.js 16 (App Router)** renders responsive user interfaces using React and TailwindCSS. **FastAPI** acts as a lightweight Python microservice providing high-speed REST API endpoints over HTTP JSON.

### 🔴 Advanced Implementation in Trajectory
- **Frontend Architecture ([`frontend/`](file:///Users/m1pro/Projects/trajectory/frontend))**: Next.js 16 App Router with client-side state management, responsive TailwindCSS glassmorphic UI, and Supabase JS browser client.
- **Backend Architecture ([`backend/`](file:///Users/m1pro/Projects/trajectory/backend))**: FastAPI server with CORS middleware, asynchronous background task execution, local Ollama LLM integration, and Pytest test suite.
