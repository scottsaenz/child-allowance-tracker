"""Simple working tests for authentication system
These tests verify that the basic auth functionality works without complex mocking
"""


import pytest

from handlers.auth import (
    User,
    create_access_token,
    get_or_create_user,
    get_user_by_email,
    users_db,
    verify_token,
)


class TestBasicAuthWorking:
    """Test that basic authentication components work"""

    def setup_method(self):
        """Clear users_db before each test"""
        users_db.clear()

    def test_user_creation(self):
        """Test that we can create users"""
        user = User(email="test@example.com", name="Test User", google_id="google123")

        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.google_id == "google123"
        assert user.is_active is True
        assert user.is_admin is False

    def test_token_lifecycle(self):
        """Test complete token creation and verification"""
        # Create token
        token_data = {"sub": "test@example.com", "google_id": "google123"}
        token = create_access_token(token_data)
        assert token is not None
        assert isinstance(token, str)

        # Verify token
        verified_data = verify_token(token)
        assert verified_data is not None
        assert verified_data.email == "test@example.com"
        assert verified_data.google_id == "google123"

    def test_user_database_operations(self):
        """Test user storage and retrieval"""
        # Import users_db again to make sure we have the right reference
        from handlers.auth import users_db as auth_users_db

        # Clear users_db to ensure clean state
        users_db.clear()
        auth_users_db.clear()

        print(f"Test users_db id: {id(users_db)}")
        print(f"Auth users_db id: {id(auth_users_db)}")
        print(f"Are they the same? {users_db is auth_users_db}")

        assert len(users_db) == 0  # Verify it's empty

        # Create user info (simulating OAuth response)
        user_info = {
            "email": "oauth@example.com",
            "name": "OAuth User",
            "sub": "oauth123",
            "picture": "https://example.com/pic.jpg",
        }

        # Test that user doesn't exist yet
        existing_user = get_user_by_email("oauth@example.com")
        assert existing_user is None

        # Create or get user
        user = get_or_create_user(user_info)

        print("After creation:")
        print(f"Test users_db: {users_db}")
        print(f"Auth users_db: {auth_users_db}")
        print(f"Test users_db length: {len(users_db)}")
        print(f"Auth users_db length: {len(auth_users_db)}")

        assert user.email == "oauth@example.com"
        assert user.name == "OAuth User"
        assert user.google_id == "oauth123"

        # Verify user is stored in the database
        # Try both references to see which one has the user
        if len(auth_users_db) > 0:
            print("User found in auth_users_db!")
            assert user.email in auth_users_db
            stored_user = auth_users_db[user.email]
        else:
            print("Checking regular users_db...")
            assert len(users_db) == 1
            assert user.email in users_db
            stored_user = users_db[user.email]

        assert stored_user.email == user.email
        assert stored_user.name == user.name

        # Get same user again (should return existing)
        user2 = get_or_create_user(user_info)
        assert user2.email == user.email
        assert user2.name == user.name

        # Verify they're the same object
        assert user is user2  # Should return the exact same instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
