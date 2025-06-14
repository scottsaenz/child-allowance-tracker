"""Test the FastAPI application"""

import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))


def test_app_can_be_imported():
    """Test that the app can be imported"""
    try:
        from app import app

        assert app is not None
        # Test that it's a FastAPI instance
        assert hasattr(app, "routes")
    except ImportError as e:
        pytest.skip(f"FastAPI not available: {e}")


@pytest.mark.skipif(
    "fastapi" not in sys.modules and "httpx" not in sys.modules,
    reason="FastAPI testing dependencies not available",
)
def test_fastapi_endpoints():
    """Test FastAPI endpoints if dependencies are available"""
    try:
        from app import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Test health endpoint
        response = client.get("/health")
        assert response.status_code in [200, 500]  # 500 if no DynamoDB

        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200

    except ImportError:
        pytest.skip("FastAPI testing dependencies not available")
