import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from adapters.adzuna import search_adzuna
from main import app


class TestAdzunaAdapter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("adapters.adzuna.os.getenv")
    def test_missing_credentials(self, mock_getenv):
        mock_getenv.return_value = None
        result = asyncio.run(search_adzuna("developer", "us"))
        self.assertEqual(result, [])

    @patch("adapters.adzuna.httpx.AsyncClient.get")
    @patch("adapters.adzuna.os.getenv")
    def test_search_adzuna_success(self, mock_getenv, mock_get):
        mock_getenv.side_effect = lambda key: {
            "ADZUNA_APP_ID": "test_id",
            "ADZUNA_APP_KEY": "test_key",
        }.get(key)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "<strong>Python</strong> Developer - Remote",
                    "company": {"display_name": "Tech Corp"},
                    "location": {"display_name": "New York, US"},
                    "redirect_url": "https://www.adzuna.com/job/123",
                    "created": "2026-07-30T10:00:00Z",
                    "description": "Work from home full time python role",
                }
            ]
        }
        mock_get.return_value = mock_response

        jobs = asyncio.run(search_adzuna("Python", "us", city="New York"))

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job["title"], "Python Developer - Remote")
        self.assertEqual(job["company"], "Tech Corp")
        self.assertEqual(job["location"], "New York, US")
        self.assertTrue(job["remote"])
        self.assertEqual(job["url"], "https://www.adzuna.com/job/123")
        self.assertEqual(job["source"], "adzuna")
        self.assertEqual(job["posted_date"], "2026-07-30T10:00:00Z")

    @patch("main.search_jooble", new_callable=AsyncMock)
    @patch("main.search_arbeitnow", new_callable=AsyncMock)
    @patch("main.search_remoteok", new_callable=AsyncMock)
    @patch("main.search_remotive", new_callable=AsyncMock)
    @patch("main.search_adzuna", new_callable=AsyncMock)
    def test_jobs_search_endpoint_modes(
        self, mock_adzuna, mock_remotive, mock_remoteok, mock_arbeitnow, mock_jooble
    ):
        mock_remotive.return_value = []
        mock_remoteok.return_value = []
        mock_arbeitnow.return_value = []
        mock_jooble.return_value = []

        mock_adzuna.return_value = [
            {
                "title": "Backend Engineer",
                "company": "FastAPI Inc",
                "location": "San Francisco",
                "remote": True,
                "url": "https://example.com/job/1",
                "source": "adzuna",
                "posted_date": "2026-07-31T00:00:00Z",
            },
            {
                "title": "Onsite Engineer",
                "company": "Building Corp",
                "location": "San Francisco",
                "remote": False,
                "url": "https://example.com/job/2",
                "source": "adzuna",
                "posted_date": "2026-07-31T00:00:00Z",
            },
            {
                "title": "Hybrid Software Developer",
                "company": "Hybrid Corp",
                "location": "London",
                "remote": False,
                "url": "https://example.com/job/3",
                "source": "adzuna",
                "posted_date": "2026-07-31T00:00:00Z",
            },
        ]

        # Test mode=remote
        res_remote = self.client.get(
            "/jobs/search?query=engineer&country=us&mode=remote"
        )
        self.assertEqual(res_remote.status_code, 200)
        jobs_remote = res_remote.json()["jobs"]
        self.assertEqual(len(jobs_remote), 1)
        self.assertEqual(jobs_remote[0]["title"], "Backend Engineer")

        # Test mode=onsite
        res_onsite = self.client.get(
            "/jobs/search?query=engineer&country=us&mode=onsite"
        )
        self.assertEqual(res_onsite.status_code, 200)
        jobs_onsite = res_onsite.json()["jobs"]
        self.assertEqual(len(jobs_onsite), 1)
        self.assertEqual(jobs_onsite[0]["title"], "Onsite Engineer")

        # Test mode=hybrid
        res_hybrid = self.client.get(
            "/jobs/search?query=engineer&country=us&mode=hybrid"
        )
        self.assertEqual(res_hybrid.status_code, 200)
        jobs_hybrid = res_hybrid.json()["jobs"]
        self.assertEqual(len(jobs_hybrid), 1)
        self.assertEqual(
            jobs_hybrid[0]["title"], "Hybrid Software Developer"
        )

        # Test no mode filter
        res_all = self.client.get("/jobs/search?query=engineer&country=us")
        self.assertEqual(res_all.status_code, 200)
        all_data = res_all.json()
        self.assertEqual(len(all_data["jobs"]), 3)
        self.assertEqual(len(all_data["external_links"]), 4)


if __name__ == "__main__":
    unittest.main()
