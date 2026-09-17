"""
Unit and integration tests for AgriClutch health and root endpoints.
Compatible with both standard unittest and pytest.
"""

import unittest
from typing import Any
from unittest.mock import AsyncMock, patch

from app.main import app
from fastapi.testclient import TestClient


class TestHealthEndpoints(unittest.TestCase):
    """Test suite for system health and liveness check endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_check(self) -> None:
        """Verify GET /health returns 200 OK and expected JSON schema."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "agriclutch-api")
        self.assertIn("version", data)
        self.assertIn("environment", data)

    def test_root_endpoint(self) -> None:
        """Verify GET / returns AgriClutch system branding and documentation sitemap."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["platform"], "AgriClutch")
        self.assertEqual(data["problem_statement"], "SIH26132")
        self.assertEqual(data["health"], "/health")
        self.assertEqual(data["health_db"], "/health/db")

    @patch("app.main.check_db_health", new_callable=AsyncMock)
    def test_database_health_connected(self, mock_check_db: Any) -> None:
        """Verify GET /health/db returns 200 when database and TimescaleDB are active."""
        mock_check_db.return_value = {
            "status": "ok",
            "connected": True,
            "scalar_check": True,
            "timescaledb": True,
            "database_url": "configured",
        }

        response = self.client.get("/health/db")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "agriclutch-api")
        self.assertTrue(data["database"]["connected"])
        self.assertTrue(data["database"]["timescaledb"])

    @patch("app.main.check_db_health", new_callable=AsyncMock)
    def test_database_health_disconnected(self, mock_check_db: Any) -> None:
        """Verify GET /health/db returns 503 when database connection is down."""
        mock_check_db.return_value = {
            "status": "disconnected",
            "connected": False,
            "error": "Connection refused",
            "timescaledb": False,
        }

        response = self.client.get("/health/db")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "disconnected")
        self.assertFalse(data["database"]["connected"])


if __name__ == "__main__":
    unittest.main()
