import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import ANALYSIS_CACHE, RESUME_CACHE, app
from services.matching_service import (
    compute_matched_jobs,
    cosine_similarity,
    rerank_jobs_with_claude,
)


class TestJobMatching(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        RESUME_CACHE.clear()
        ANALYSIS_CACHE.clear()

    def test_cosine_similarity(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(v1, v2), 1.0)

        v3 = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(v1, v3), 0.0)

        self.assertEqual(cosine_similarity([], [1.0]), 0.0)

    def test_compute_matched_jobs_top_20(self):
        profile = {
            "skills": ["Python", "FastAPI"],
            "tools": ["Docker"],
            "suggested_roles": ["Backend Engineer"],
            "embedding": [1.0, 0.5, 0.0] * 128,
        }

        jobs = []
        for i in range(30):
            jobs.append(
                {
                    "title": f"Job {i} - Python Engineer",
                    "company": f"Company {i}",
                    "location": "Remote",
                    "source": "test",
                }
            )

        matched = compute_matched_jobs(profile, jobs)
        self.assertEqual(len(matched), 20)
        self.assertIn("similarity_score", matched[0])

    @patch("services.matching_service.query_ollama", new_callable=AsyncMock)
    def test_rerank_jobs_with_claude(self, mock_query_ollama):
        mock_query_ollama.return_value = (
            '[{"id": 1, "fit_score": 98, "reasoning": "Top seniority match"}, '
            '{"id": 0, "fit_score": 85, "reasoning": "Good skill match"}]'
        )

        profile = {
            "skills": ["Python", "FastAPI"],
            "tools": ["Docker"],
            "years_of_experience": 5.0,
            "suggested_roles": ["Senior Backend Developer"],
        }
        jobs = [
            {
                "title": "Junior Python Dev",
                "company": "Company A",
                "similarity_score": 0.8,
            },
            {
                "title": "Senior Python Engineer",
                "company": "Company B",
                "similarity_score": 0.85,
            },
        ]

        reranked = asyncio.run(rerank_jobs_with_claude(profile, jobs))

        self.assertEqual(len(reranked), 2)
        self.assertEqual(reranked[0]["title"], "Senior Python Engineer")
        self.assertEqual(reranked[0]["fit_score"], 98)

    @patch("main.search_jobs", new_callable=AsyncMock)
    @patch("main.analyze_resume_agent", new_callable=AsyncMock)
    def test_matched_jobs_endpoint(self, mock_agent, mock_search):
        mock_agent.return_value = {
            "file_reference_id": "ref-999",
            "skills": ["Python", "FastAPI"],
            "tools": ["Docker"],
            "years_of_experience": 4.0,
            "suggested_roles": ["Backend Developer"],
            "embedding": [0.5] * 384,
        }

        mock_search.return_value = {
            "jobs": [
                {
                    "title": "Python Developer",
                    "company": "FastAPI Corp",
                    "location": "Remote",
                    "remote": True,
                    "url": "https://example.com/job/1",
                    "source": "adzuna",
                    "posted_date": "2026-07-31T10:00:00Z",
                }
            ],
            "external_links": [],
        }

        RESUME_CACHE["ref-999"] = {
            "text": "Python Developer resume text",
            "user_id": "user_1",
        }

        response = self.client.get("/jobs/matched?file_reference_id=ref-999&query=python")
        self.assertEqual(response.status_code, 200)

        json_resp = response.json()
        self.assertIn("matched_jobs", json_resp)
        self.assertIn("total_matched", json_resp)
        self.assertEqual(json_resp["file_reference_id"], "ref-999")
        self.assertGreater(json_resp["total_matched"], 0)

        matched_job = json_resp["matched_jobs"][0]
        self.assertIn("fit_score", matched_job)
        self.assertIn("reasoning", matched_job)

    def test_matched_jobs_endpoint_not_found(self):
        response = self.client.get("/jobs/matched?file_reference_id=unknown_ref&query=python")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
