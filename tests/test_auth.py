"""Tests for authentication module"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from freezegun import freeze_time
from jose import jwt  # Changed from 'import jwt' to 'from jose import jwt'

from handlers.auth import (
    ALGORITHM,
    SECRET_KEY,
    TokenData,
    User,
    create_access_token,
    create_user,
    get_authorized_emails,
    get_current_user,
    get_current_user_optional,
    get_or_create_user,
    get_user_by_email,
    is_user_authorized,
    users_db,
    verify_token,
)


class TestJWTFunctions:
    """Test JWT token creation and verification"""

    def test_create_access_token_default_expiry(self):
        """Test creating JWT token with default expiry"""
        data = {"sub": "test@example.com", "google_id": "123456"}
        token = create_access_token(data)

        # Verify token structure
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts

        # Decode and verify payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert payload["google_id"] == "123456"
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self):
        """Test creating JWT token with custom expiry"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=30)

        with freeze_time("2025-01-01 12:00:00"):
            token = create_access_token(data, expires_delta)
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            expected_exp = datetime(2025, 1, 1, 12, 30, 0).timestamp()
            assert payload["exp"] == expected_exp

    def test_verify_token_valid(self):
        """Test verifying a valid token"""
        data = {"sub": "test@example.com", "google_id": "123456"}
        token = create_access_token(data)

        token_data = verify_token(token)

        assert isinstance(token_data, TokenData)
        assert token_data.email == "test@example.com"
        assert token_data.google_id == "123456"

    def test_verify_token_expired(self):
        """Test verifying an expired token"""
        data = {"sub": "test@example.com"}

        with freeze_time("2025-01-01 12:00:00"):
            expires_delta = timedelta(minutes=-30)  # Already expired
            token = create_access_token(data, expires_delta)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)

    def test_verify_token_invalid_signature(self):
        """Test verifying token with invalid signature"""
        invalid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIn0.invalid_signature"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_verify_token_missing_sub(self):
        """Test token verification with missing sub claim"""
        # Create token without sub claim
        payload = {
            "google_id": "google123",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        # Should raise HTTPException for missing sub
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail


class TestUserManagement:
    """Test user management functions"""

    def setup_method(self):
        """Clear users_db before each test"""
        users_db.clear()

    def test_create_user(self):
        """Test creating a new user"""
        user_info = {
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
            "sub": "google123456",
        }

        with freeze_time("2025-01-01 12:00:00"):
            user = create_user(user_info)

        assert isinstance(user, User)
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.picture == "https://example.com/avatar.jpg"
        assert user.google_id == "google123456"
        assert user.is_active is True
        assert user.created_at == datetime(2025, 1, 1, 12, 0, 0)

        # Verify user is stored in database
        assert users_db["test@example.com"] == user

    def test_get_user_by_email_exists(self):
        """Test getting existing user by email"""
        user = User(email="test@example.com", name="Test User", google_id="123456")
        users_db["test@example.com"] = user

        result = get_user_by_email("test@example.com")
        assert result == user

    def test_get_user_by_email_not_exists(self):
        """Test getting non-existent user by email"""
        result = get_user_by_email("nonexistent@example.com")
        assert result is None

    def test_get_or_create_user_existing(self):
        """Test get_or_create with existing user"""
        existing_user = User(
            email="test@example.com", name="Existing User", google_id="123456"
        )
        users_db["test@example.com"] = existing_user

        user_info = {
            "email": "test@example.com",
            "name": "New Name",  # Different name
            "sub": "123456",
        }

        result = get_or_create_user(user_info)
        assert result == existing_user
        assert result.name == "Existing User"  # Should keep existing data

    def test_get_or_create_user_new(self):
        """Test get_or_create with new user"""
        user_info = {"email": "new@example.com", "name": "New User", "sub": "789012"}

        result = get_or_create_user(user_info)
        assert isinstance(result, User)
        assert result.email == "new@example.com"
        assert result.name == "New User"
        assert result.google_id == "789012"
        assert users_db["new@example.com"] == result


class TestAuthenticationDependencies:
    """Test FastAPI dependency functions"""

    def setup_method(self):
        """Clear users_db before each test"""
        users_db.clear()

    @pytest.mark.asyncio
    async def test_get_current_user_valid(self):
        """Test getting current user with valid token"""
        # Create user
        user = User(email="test@example.com", name="Test User", google_id="123456")
        users_db["test@example.com"] = user

        # Create token
        token = create_access_token({"sub": "test@example.com", "google_id": "123456"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        result = await get_current_user(credentials)
        assert result == user

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Test getting current user when user doesn't exist in database"""
        token = create_access_token(
            {"sub": "nonexistent@example.com", "google_id": "123456"}
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self):
        """Test getting current user when user is inactive"""
        user = User(
            email="test@example.com",
            name="Test User",
            google_id="123456",
            is_active=False,
        )
        users_db["test@example.com"] = user

        token = create_access_token({"sub": "test@example.com", "google_id": "123456"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Inactive user" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_token(self):
        """Test optional authentication with valid token"""
        user = User(email="test@example.com", name="Test User", google_id="123456")
        users_db["test@example.com"] = user

        token = create_access_token({"sub": "test@example.com", "google_id": "123456"})

        # Mock request with Authorization header
        request = Mock()
        request.headers = {"Authorization": f"Bearer {token}"}

        result = await get_current_user_optional(request)
        assert result == user

    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_token(self):
        """Test optional authentication without token"""
        request = Mock()
        request.headers = {}

        result = await get_current_user_optional(request)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_invalid_token(self):
        """Test optional authentication with invalid token"""
        request = Mock()
        request.headers = {"Authorization": "Bearer invalid_token"}

        result = await get_current_user_optional(request)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_admin_user_valid_admin(self):
        """Test admin authentication with valid admin user"""
        admin_user = User(
            email="admin@example.com", name="Admin User", google_id="123456"
        )

        # Set the environment variable properly for this test
        with patch.dict(
            "os.environ", {"ADMIN_EMAILS": "admin@example.com,other@example.com"}
        ):
            # Import the function with updated environment
            import importlib

            import handlers.auth

            importlib.reload(handlers.auth)
            from handlers.auth import get_admin_user as get_admin_user_updated

            result = await get_admin_user_updated(admin_user)
            assert result == admin_user

    @pytest.mark.asyncio
    async def test_get_admin_user_not_admin(self):
        """Test admin authentication with non-admin user"""
        regular_user = User(
            email="user@example.com", name="Regular User", google_id="123456"
        )

        with patch.dict("os.environ", {"ADMIN_EMAILS": "admin@example.com"}):
            import importlib

            import handlers.auth

            importlib.reload(handlers.auth)
            from handlers.auth import get_admin_user as get_admin_user_updated

            with pytest.raises(HTTPException) as exc_info:
                await get_admin_user_updated(regular_user)

            assert exc_info.value.status_code == 403
            assert "Admin access required" in str(exc_info.value.detail)


class TestLegacyAuthFunctions:
    """Test backward compatibility functions"""

    def test_get_authorized_emails_from_env(self):
        """Test getting authorized emails from environment"""
        with patch.dict(
            "os.environ",
            {
                "AUTHORIZED_EMAILS": "user1@example.com, user2@example.com, user3@example.com"
            },
        ):
            emails = get_authorized_emails()
            assert emails == [
                "user1@example.com",
                "user2@example.com",
                "user3@example.com",
            ]

    def test_get_authorized_emails_empty(self):
        """Test getting authorized emails when none set"""
        with patch.dict("os.environ", {}, clear=True):
            emails = get_authorized_emails()
            assert emails == ["development@example.com"]

    def test_is_user_authorized_valid(self):
        """Test user authorization check"""
        with patch.dict(
            "os.environ", {"AUTHORIZED_EMAILS": "user@example.com,admin@example.com"}
        ):
            assert is_user_authorized("user@example.com") is True
            assert is_user_authorized("USER@EXAMPLE.COM") is True  # Case insensitive
            assert is_user_authorized("unauthorized@example.com") is False


class TestOAuthSetup:
    """Test OAuth configuration"""

    def test_setup_oauth_with_credentials_functional(self):
        """Test OAuth setup with valid credentials - functional test"""
        with patch.dict(
            "os.environ",
            {
                "GOOGLE_CLIENT_ID": "test_client_id",
                "GOOGLE_CLIENT_SECRET": "test_client_secret",
            },
        ):
            from handlers.auth import oauth, setup_oauth

            # Should run without errors
            setup_oauth()

            # OAuth should be configured
            assert oauth is not None
            # This is the key test - no exceptions means success
            assert True

    def test_setup_oauth_missing_credentials_functional(self):
        """Test OAuth setup without credentials - functional test"""
        with patch.dict("os.environ", {}, clear=True):
            from handlers.auth import oauth, setup_oauth

            # Should run without errors even with missing credentials
            setup_oauth()

            # OAuth should still exist but not be fully configured
            assert oauth is not None
            # This is the key test - no exceptions means graceful handling
            assert True

    def test_oauth_environment_detection(self):
        """Test that OAuth properly detects environment variables"""

        # Test with environment variables set
        with patch.dict(
            "os.environ",
            {
                "GOOGLE_CLIENT_ID": "test_client_id",
                "GOOGLE_CLIENT_SECRET": "test_client_secret",
            },
        ):
            # Re-import to get fresh values
            import importlib

            import handlers.auth

            importlib.reload(handlers.auth)

            # Should have the test values
            assert handlers.auth.GOOGLE_CLIENT_ID == "test_client_id"
            assert handlers.auth.GOOGLE_CLIENT_SECRET == "test_client_secret"


class TestUserModel:
    """Test User model validation"""

    def test_user_model_creation(self):
        """Test creating User model with all fields"""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
            "google_id": "123456789",
            "is_active": True,
            "created_at": datetime(2025, 1, 1, 12, 0, 0),
        }

        user = User(**user_data)
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.picture == "https://example.com/pic.jpg"
        assert user.google_id == "123456789"
        assert user.is_active is True
        assert user.created_at == datetime(2025, 1, 1, 12, 0, 0)

    def test_user_model_minimal(self):
        """Test user model with minimal required fields"""
        user = User(
            email="test@example.com",
            name="Test User",
            google_id="123456789",
            created_at=None,  # Explicitly set to None to test the behavior
        )

        # After __post_init__, created_at should be set
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
        assert user.is_active is True
        assert user.is_admin is False
        assert user.picture is None

    def test_token_data_model(self):
        """Test TokenData model"""
        token_data = TokenData(email="test@example.com", google_id="123456")
        assert token_data.email == "test@example.com"
        assert token_data.google_id == "123456"


if __name__ == "__main__":
    pytest.main([__file__])
