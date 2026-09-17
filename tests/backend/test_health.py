"""
Backend integration test for AgriClutch health and root endpoints.
Run from repository root or backend workspace.
"""

import sys
import os
import unittest
from unittest.mock import AsyncMock, patch

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app


class TestBackendHealth(unittest.TestCase):
    """Verifies health probes and system readiness."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_probe(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["service"], "agriclutch-api")

    def test_root_probe(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["platform"], "AgriClutch")

    @patch("app.main.check_db_health", new_callable=AsyncMock)
    def test_db_health_mocked_connected(self, mock_check_db):
        mock_check_db.return_value = {
            "status": "ok",
            "connected": True,
            "scalar_check": True,
            "timescaledb": True,
        }
        response = self.client.get("/health/db")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["database"]["connected"])


if __name__ == "__main__":
    unittest.main()
