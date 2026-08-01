import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from agents.resume_analyzer import (
    analyze_resume_agent,
    embed_profile,
    extract_skills,
    infer_role,
)
from main import app


class TestResumeAnalyzerAgent(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("agents.resume_analyzer.query_ollama", new_callable=AsyncMock)
    def test_extract_skills_node_success(self, mock_query_ollama):
        mock_query_ollama.return_value = """{
            "highest_education": "Bachelor of Science in Computer Science",
            "skills": ["Python", "FastAPI"],
            "tools": ["Git", "Docker"],
            "seniority_level": "Software Engineer",
            "suggested_roles": ["Backend Developer", "Python Engineer", "API Lead"],
            "summary_pitch": "Experienced developer.",
            "key_strengths": ["Strength 1", "Strength 2", "Strength 3"],
            "top_recommendations": ["Rec 1", "Rec 2", "Rec 3"]
        }"""

        res = asyncio.run(
            extract_skills({"resume_text": "Experienced Python Developer with BS in Computer Science"})
        )
        self.assertEqual(res["skills"], ["Python", "FastAPI"])
        self.assertEqual(res["tools"], ["Git", "Docker"])
        self.assertEqual(res["highest_education"], "Bachelor of Science in Computer Science")
        self.assertIsNone(res["error"])

    def test_extract_skills_node_empty_resume_text(self):
        res = asyncio.run(extract_skills({"resume_text": "   "}))
        self.assertEqual(res["skills"], [])
        self.assertIsNotNone(res["error"])

    @patch("agents.resume_analyzer.asyncio.sleep", new_callable=AsyncMock)
    @patch("agents.resume_analyzer.query_ollama", new_callable=AsyncMock)
    def test_extract_skills_node_retries_then_fails(self, mock_query_ollama, mock_sleep):
        mock_query_ollama.return_value = ""  # empty response

        res = asyncio.run(extract_skills({"resume_text": "Some resume text here"}))
        self.assertEqual(res["skills"], [])
        self.assertIsNotNone(res["error"])
        self.assertEqual(mock_query_ollama.call_count, 2)  # MAX_ANALYSIS_ATTEMPTS

    def test_infer_role_node_passthrough(self):
        res = asyncio.run(
            infer_role(
                {
                    "highest_education": "Master of Science in Software Engineering",
                    "skills": ["Python", "FastAPI"],
                    "tools": ["Git"],
                    "suggested_roles": ["Backend Developer", "Python Engineer", "API Lead"],
                }
            )
        )
        self.assertEqual(len(res["suggested_roles"]), 3)
        self.assertIn("Backend Developer", res["suggested_roles"])

    def test_infer_role_node_missing_roles(self):
        res = asyncio.run(infer_role({"highest_education": "BS in Computer Science"}))
        self.assertEqual(res["suggested_roles"], [])

    def test_embed_profile_node(self):
        state = {
            "highest_education": "Bachelor of Science in Computer Science",
            "skills": ["Python", "FastAPI"],
            "tools": ["Git", "Docker"],
            "suggested_roles": ["Backend Developer"],
            "file_reference_id": "test_ref_id",
            "user_id": "user_1",
        }
        res = asyncio.run(embed_profile(state))
        self.assertIn("embedding", res)
        self.assertIsInstance(res["embedding"], list)
        self.assertGreater(len(res["embedding"]), 0)

    @patch("main.analyze_resume_agent", new_callable=AsyncMock)
    def test_resume_analyze_endpoint(self, mock_agent):
        mock_agent.return_value = {
            "file_reference_id": "ref-123",
            "highest_education": "Bachelor of Science in Computer Science",
            "skills": ["Python", "FastAPI"],
            "tools": ["Git", "Docker"],
            "suggested_roles": ["Backend Engineer", "API Architect"],
            "stored_in_supabase": True,
        }

        payload = {
            "file_reference_id": "ref-123",
            "resume_text": "BS in Computer Science, Senior Python Backend Developer",
        }
        response = self.client.post("/resume/analyze", json=payload)
        self.assertEqual(response.status_code, 200)

        json_resp = response.json()
        self.assertEqual(json_resp["file_reference_id"], "ref-123")
        self.assertEqual(json_resp["skills"], ["Python", "FastAPI"])
        self.assertEqual(len(json_resp["suggested_roles"]), 2)

    def test_resume_analyze_endpoint_not_found(self):
        payload = {"file_reference_id": "nonexistent_ref_id"}
        response = self.client.post("/resume/analyze", json=payload)
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()