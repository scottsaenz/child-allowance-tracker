"""Test configuration and fixtures"""

import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    test_env = {
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "GOOGLE_CLIENT_ID": "test-google-client-id",
        "GOOGLE_CLIENT_SECRET": "test-google-client-secret",
        "GOOGLE_REDIRECT_URI": "http://localhost:8000/auth/callback",
        "ADMIN_EMAILS": "admin@example.com",
        "AUTHORIZED_EMAILS": "test@example.com,admin@example.com",
        "ENVIRONMENT": "testing",
    }

    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def clean_users_db():
    """Fixture to clean users database before tests"""
    from handlers.auth import users_db

    users_db.clear()
    yield
    users_db.clear()
