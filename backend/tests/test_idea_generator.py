import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from agents.idea_generator import (
    generate_ideas_agent,
    generate_project_ideas,
    identify_skill_gaps,
)
from main import ANALYSIS_CACHE, RESUME_CACHE, app


class TestIdeaGeneratorAgent(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        RESUME_CACHE.clear()
        ANALYSIS_CACHE.clear()

    @patch("agents.idea_generator.anthropic.AsyncAnthropic")
    def test_identify_skill_gaps_node(self, mock_anthropic_cls):
        mock_client = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.content = [
            MagicMock(
                text='{"skill_gaps": ["Docker Containerization", "Redis Caching", "CI/CD Pipelines"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        with patch("agents.idea_generator.os.getenv", return_value="dummy_key"):
            res = asyncio.run(
                identify_skill_gaps(
                    {"skills": ["Python", "FastAPI"], "target_roles": ["Backend Lead"]}
                )
            )
            self.assertEqual(len(res["skill_gaps"]), 3)
            self.assertIn("Docker Containerization", res["skill_gaps"])

    @patch("agents.idea_generator.anthropic.AsyncAnthropic")
    def test_generate_project_ideas_node(self, mock_anthropic_cls):
        mock_client = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.content = [
            MagicMock(
                text="""{
  "project_ideas": [
    {
      "title": "Real-time Redis Task Queue",
      "description": "Build an async background task worker that processes document pipelines.",
      "suggested_stack": ["Python", "FastAPI", "Redis", "Docker"],
      "difficulty": "Intermediate",
      "estimated_hours": 20
    }
  ]
}"""
            )
        ]
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        with patch("agents.idea_generator.os.getenv", return_value="dummy_key"):
            res = asyncio.run(
                generate_project_ideas(
                    {
                        "skills": ["Python", "FastAPI"],
                        "target_roles": ["Backend Developer"],
                        "skill_gaps": ["Redis Caching"],
                    }
                )
            )
            ideas = res["project_ideas"]
            self.assertEqual(len(ideas), 1)

            idea = ideas[0]
            self.assertEqual(idea["title"], "Real-time Redis Task Queue")
            self.assertIn("description", idea)
            self.assertIn("suggested_stack", idea)
            self.assertEqual(idea["difficulty"], "Intermediate")
            self.assertEqual(idea["estimated_hours"], 20)

    @patch("main.generate_ideas_agent", new_callable=AsyncMock)
    def test_ideas_generate_endpoint_with_body(self, mock_agent):
        mock_agent.return_value = {
            "file_reference_id": None,
            "skills": ["Python", "FastAPI"],
            "target_roles": ["Backend Engineer"],
            "skill_gaps": ["Docker", "Redis"],
            "project_ideas": [
                {
                    "title": "Async Task Queue",
                    "description": "Background worker system.",
                    "suggested_stack": ["Python", "FastAPI", "Redis"],
                    "difficulty": "Intermediate",
                    "estimated_hours": 15,
                }
            ],
        }

        payload = {
            "skills": ["Python", "FastAPI"],
            "target_roles": ["Backend Engineer"],
        }
        response = self.client.post("/ideas/generate", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["project_ideas"]), 1)
        self.assertEqual(data["project_ideas"][0]["title"], "Async Task Queue")

    @patch("main.generate_ideas_agent", new_callable=AsyncMock)
    def test_ideas_generate_endpoint_with_ref_id(self, mock_agent):
        ANALYSIS_CACHE["ref-123"] = {
            "skills": ["Python", "React"],
            "suggested_roles": ["Full Stack Engineer"],
        }

        mock_agent.return_value = {
            "file_reference_id": "ref-123",
            "skills": ["Python", "React"],
            "target_roles": ["Full Stack Engineer"],
            "skill_gaps": ["PostgreSQL Optimization"],
            "project_ideas": [
                {
                    "title": "Full Stack Analytics Dashboard",
                    "description": "Realtime metric portal.",
                    "suggested_stack": ["Python", "React", "Next.js"],
                    "difficulty": "Advanced",
                    "estimated_hours": 30,
                }
            ],
        }

        payload = {"file_reference_id": "ref-123"}
        response = self.client.post("/ideas/generate", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["file_reference_id"], "ref-123")
        self.assertEqual(len(data["project_ideas"]), 1)

    def test_ideas_generate_endpoint_missing_parameters(self):
        response = self.client.post("/ideas/generate", json={})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
