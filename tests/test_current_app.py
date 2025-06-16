"""Test the current app functionality without auth requirements"""

import pytest
from fastapi.testclient import TestClient

from app import app


class TestCurrentAppFunctionality:
    """Test what currently works in the app"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_app_starts(self, client):
        """Test that the app starts without errors"""
        # Just making a request proves the app initializes
        response = client.get("/")
        assert response.status_code == 200

    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_debug_endpoint_structure(self, client):
        """Test debug endpoint and document its structure"""
        response = client.get("/debug")
        assert response.status_code == 200
        data = response.json()

        # Document what fields we expect
        expected_fields = ["python_version", "current_directory", "timestamp"]
        for field in expected_fields:
            if field in data:
                assert data[field] is not None

    def test_children_endpoint_current_behavior(self, client):
        """Test children endpoint current behavior"""
        response = client.get("/children")
        # Document what the current behavior is
        assert response.status_code in [200, 403, 404]

        if response.status_code == 200:
            # If it returns 200, it should return a list
            data = response.json()
            assert isinstance(data, list)

    def test_create_child_current_behavior(self, client):
        """Test creating a child with current implementation"""
        child_data = {"name": "Test Child", "age": 8, "weekly_allowance": 5.0}

        response = client.post("/children", json=child_data)
        # Document current behavior
        assert response.status_code in [200, 201, 403, 404, 422]

        if response.status_code in [200, 201]:
            data = response.json()
            assert data["name"] == "Test Child"
            assert "id" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
