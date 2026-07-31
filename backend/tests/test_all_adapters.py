import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from adapters import (
    search_adzuna,
    search_arbeitnow,
    search_jooble,
    search_remoteok,
    search_remotive,
)
from adapters.utils import (
    clean_text,
    deduplicate_jobs,
    is_remote_heuristic,
    normalize_date,
    sort_jobs_by_date,
)
from main import app


class TestJobAdapters(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_utils_clean_text(self):
        self.assertEqual(clean_text("<b>Python</b> Developer&nbsp;"), "Python Developer")
        self.assertEqual(clean_text(None), "")

    def test_utils_remote_heuristic(self):
        self.assertTrue(is_remote_heuristic("Python Dev", "Remote, US"))
        self.assertTrue(is_remote_heuristic("Work from Home - Backend", "New York"))
        self.assertFalse(is_remote_heuristic("Software Engineer", "San Francisco, CA"))

    def test_utils_normalize_date(self):
        self.assertEqual(normalize_date(1785000000), "2026-07-25T17:20:00Z")
        self.assertEqual(normalize_date("2026-07-30T10:00:00Z"), "2026-07-30T10:00:00Z")

    def test_deduplicate_jobs(self):
        jobs = [
            {"title": "Software Engineer", "company": "Acme Corp", "source": "adzuna"},
            {"title": "software engineer", "company": "ACME CORP.", "source": "remotive"},
            {"title": "Data Scientist", "company": "Beta Inc", "source": "jooble"},
        ]
        deduped = deduplicate_jobs(jobs)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["source"], "adzuna")
        self.assertEqual(deduped[1]["source"], "jooble")

    def test_sort_jobs_by_date(self):
        jobs = [
            {"title": "Job A", "posted_date": "2026-07-01T00:00:00Z"},
            {"title": "Job B", "posted_date": "2026-07-30T00:00:00Z"},
            {"title": "Job C", "posted_date": ""},
        ]
        sorted_jobs = sort_jobs_by_date(jobs)
        self.assertEqual(sorted_jobs[0]["title"], "Job B")
        self.assertEqual(sorted_jobs[1]["title"], "Job A")
        self.assertEqual(sorted_jobs[2]["title"], "Job C")

    @patch("adapters.remotive.httpx.AsyncClient.get")
    def test_search_remotive(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "jobs": [
                {
                    "title": "Backend Dev",
                    "company_name": "Remotive Co",
                    "candidate_required_location": "Worldwide",
                    "url": "https://remotive.com/job/1",
                    "publication_date": "2026-07-30T12:00:00",
                }
            ]
        }
        mock_get.return_value = mock_response

        jobs = asyncio.run(search_remotive("Backend"))
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Backend Dev")
        self.assertEqual(jobs[0]["source"], "remotive")
        self.assertTrue(jobs[0]["remote"])

    @patch("adapters.remoteok.httpx.AsyncClient.get")
    def test_search_remoteok(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {"legal": "Notice"},
            {
                "id": "123",
                "position": "Python Engineer",
                "company": "RemoteOK Ltd",
                "location": "Worldwide",
                "url": "https://remoteok.com/job/123",
                "date": "2026-07-29T10:00:00Z",
                "tags": ["python"],
            },
        ]
        mock_get.return_value = mock_response

        jobs = asyncio.run(search_remoteok("Python"))
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["company"], "RemoteOK Ltd")
        self.assertEqual(jobs[0]["source"], "remoteok")

    @patch("adapters.arbeitnow.httpx.AsyncClient.get")
    def test_search_arbeitnow(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "title": "Fullstack Developer",
                    "company_name": "Arbeit Co",
                    "location": "Berlin",
                    "remote": True,
                    "url": "https://arbeitnow.com/job/1",
                    "created_at": 1785000000,
                }
            ]
        }
        mock_get.return_value = mock_response

        jobs = asyncio.run(search_arbeitnow("Fullstack"))
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source"], "arbeitnow")
        self.assertTrue(jobs[0]["remote"])

    @patch("adapters.jooble.httpx.AsyncClient.post")
    @patch("adapters.jooble.os.getenv")
    def test_search_jooble(self, mock_getenv, mock_post):
        mock_getenv.return_value = "dummy_jooble_key"
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "jobs": [
                {
                    "title": "DevOps Engineer",
                    "company": "Jooble Inc",
                    "location": "New York, NY",
                    "link": "https://jooble.org/job/1",
                    "updated": "2026-07-31T08:00:00",
                    "snippet": "Remote DevOps role",
                }
            ]
        }
        mock_post.return_value = mock_response

        jobs = asyncio.run(search_jooble("DevOps", country="us", city="New York"))
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source"], "jooble")
        self.assertTrue(jobs[0]["remote"])

    @patch("main.search_adzuna", new_callable=AsyncMock)
    @patch("main.search_remotive", new_callable=AsyncMock)
    @patch("main.search_remoteok", new_callable=AsyncMock)
    @patch("main.search_arbeitnow", new_callable=AsyncMock)
    @patch("main.search_jooble", new_callable=AsyncMock)
    def test_concurrent_search_endpoint(
        self, mock_jooble, mock_arbeitnow, mock_remoteok, mock_remotive, mock_adzuna
    ):
        mock_adzuna.return_value = [
            {
                "title": "Senior Python Engineer",
                "company": "Acme Corp",
                "location": "Remote, US",
                "remote": True,
                "url": "https://adzuna.com/job/1",
                "source": "adzuna",
                "posted_date": "2026-07-31T10:00:00Z",
            }
        ]
        mock_remotive.return_value = [
            {
                "title": "senior python engineer",
                "company": "acme corp.",
                "location": "Worldwide",
                "remote": True,
                "url": "https://remotive.com/job/1",
                "source": "remotive",
                "posted_date": "2026-07-30T10:00:00Z",
            }
        ]
        mock_remoteok.return_value = [
            {
                "title": "Frontend Lead",
                "company": "Design Co",
                "location": "Onsite, NY",
                "remote": False,
                "url": "https://remoteok.com/job/2",
                "source": "remoteok",
                "posted_date": "2026-07-31T12:00:00Z",
            }
        ]
        mock_arbeitnow.return_value = []
        mock_jooble.return_value = []

        res = self.client.get("/jobs/search?query=engineer&country=us")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "Frontend Lead")
        self.assertEqual(data[1]["title"], "Senior Python Engineer")

        res_remote = self.client.get("/jobs/search?query=engineer&country=us&mode=remote")
        self.assertEqual(res_remote.status_code, 200)
        remote_data = res_remote.json()
        self.assertEqual(len(remote_data), 1)
        self.assertEqual(remote_data[0]["title"], "Senior Python Engineer")


if __name__ == "__main__":
    unittest.main()
