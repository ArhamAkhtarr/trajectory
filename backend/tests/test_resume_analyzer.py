import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from agents.resume_analyzer import (
    _detect_domain_profile,
    analyze_resume_agent,
    embed_profile,
    extract_skills,
    infer_role,
)
from main import app


class TestResumeAnalyzerAgent(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_detect_domain_profile_electrical(self):
        text = "Bachelor of Science in Electrical Engineering. Skilled in PCB design, circuit analysis, Proteus, LTspice, and microcontrollers."
        profile = _detect_domain_profile(text)
        self.assertEqual(profile["seniority_level"], "Electrical Engineer")
        self.assertIn("Circuit Design & Analysis", profile["skills"])
        self.assertIn("Proteus", profile["tools"])

    def test_detect_domain_profile_mechanical(self):
        text = "BS in Mechanical Engineering with SolidWorks 3D CAD modeling, thermodynamics, FEA stress analysis, and Ansys simulation."
        profile = _detect_domain_profile(text)
        self.assertEqual(profile["seniority_level"], "Mechanical Engineer")
        self.assertIn("Computer-Aided Design (CAD)", profile["skills"])
        self.assertIn("SolidWorks", profile["tools"])

    def test_detect_domain_profile_biomedical(self):
        text = "Biomedical Engineering graduate specializing in medical device design, biosignals, LabVIEW, FDA compliance, and biomechanics."
        profile = _detect_domain_profile(text)
        self.assertEqual(profile["seniority_level"], "Biomedical Engineer")
        self.assertIn("Medical Device Design", profile["skills"])
        self.assertIn("LabVIEW", profile["tools"])

    @patch("agents.resume_analyzer.anthropic.AsyncAnthropic")
    def test_extract_skills_node(self, mock_anthropic_cls):
        mock_client = AsyncMock()
        mock_msg = MagicMock()
        mock_block = MagicMock()
        mock_block.type = "tool_use"
        mock_block.name = "submit_resume_analysis"
        mock_block.input = {
            "highest_education": "Bachelor of Science in Computer Science",
            "skills": ["Python", "FastAPI"],
            "tools": ["Git", "Docker"],
            "seniority_level": "Software Engineer",
            "suggested_roles": ["Backend Developer", "Python Engineer", "API Lead"],
            "summary_pitch": "Experienced developer.",
            "key_strengths": ["Strength 1", "Strength 2", "Strength 3"],
            "top_recommendations": ["Rec 1", "Rec 2", "Rec 3"],
        }
        mock_msg.content = [mock_block]
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        with patch("agents.resume_analyzer.os.getenv", return_value="dummy_key"):
            res = asyncio.run(extract_skills({"resume_text": "Experienced Python Developer with BS in Computer Science"}))
            self.assertEqual(res["skills"], ["Python", "FastAPI"])
            self.assertEqual(res["tools"], ["Git", "Docker"])
            self.assertEqual(res["highest_education"], "Bachelor of Science in Computer Science")

    @patch("agents.resume_analyzer.anthropic.AsyncAnthropic")
    def test_infer_role_node(self, mock_anthropic_cls):
        mock_client = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.content = []
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        with patch("agents.resume_analyzer.os.getenv", return_value="dummy_key"):
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
