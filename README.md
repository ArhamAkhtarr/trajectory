# Trajectory Monorepo

`trajectory` is a monorepo containing a **Next.js 14** frontend and a **FastAPI** backend.

## Project Structure

```
trajectory/
├── backend/            # FastAPI Python 3.11+ application
│   ├── main.py         # Main FastAPI application with /health endpoint
│   ├── requirements.txt# Python dependencies (fastapi, uvicorn, httpx, pydantic, python-dotenv)
│   └── .env.example    # Environment variable placeholders
├── frontend/           # Next.js 14 App Router, TypeScript, Tailwind CSS, shadcn/ui frontend
└── README.md           # Monorepo documentation
```

---

## Getting Started

### 1. Prerequisites

- **Python**: 3.11+
- **Node.js**: v18+ (Node.js v20 recommended)
- **npm** or **pnpm** / **yarn** / **bun**

---

### 2. Setting Up & Running the Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

5. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend API will be available at [http://localhost:8000](http://localhost:8000).  
   Verify the health endpoint at [http://localhost:8000/health](http://localhost:8000/health) or via curl:
   ```bash
   curl http://localhost:8000/health
   # Returns: {"status":"ok"}
   ```

---

### 3. Setting Up & Running the Frontend

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   The frontend will be running at [http://localhost:3000](http://localhost:3000).

---

## Environment Variables

Refer to `backend/.env.example` for required backend environment variables:
- `ADZUNA_APP_ID`
- `ADZUNA_APP_KEY`
- `JOOBLE_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `ANTHROPIC_API_KEY`
