import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from services.database import DynamoDBService
from services.google_sheets import GoogleSheetsService


@pytest.fixture
def google_sheets_service():
    """Create a GoogleSheetsService instance for testing"""
    return GoogleSheetsService()


@pytest.fixture
def database_service():
    """Create a DynamoDBService instance for testing"""
    return DynamoDBService()


def test_google_sheets_service_init():
    """Test GoogleSheetsService initialization"""
    service = GoogleSheetsService()
    assert service is not None


def test_get_allowance_data():
    """Test getting allowance data"""
    service = GoogleSheetsService()
    data = service.get_allowance_data()
    assert isinstance(data, list)


def test_add_expenditure():
    """Test adding expenditure"""
    service = GoogleSheetsService()
    result = service.add_expenditure("child1", 5.00, "2024-06-25", "Test")
    assert result is True


def test_calculate_total_earned(google_sheets_service):
    """Test calculating total earned from allowance data"""
    data = google_sheets_service.get_allowance_data()
    assert isinstance(data, list)

    # Test with mock data
    total_child1 = sum(
        row.get("child1", 0) for row in data if row.get("Before Today", False)
    )
    assert isinstance(total_child1, int | float)


def test_calculate_total_spent(database_service):
    """Test calculating total spent from database"""
    total_spent = database_service.get_total_spent("child1")
    assert isinstance(total_spent, int | float)
    assert total_spent >= 0


def test_post_expenditure(database_service):
    """Test posting an expenditure"""
    result = database_service.save_expenditure(
        "child1", 10.50, "2024-06-25", "Test expenditure"
    )
    assert result is True

    # Verify it was saved
    expenditures = database_service.get_expenditures("child1")
    assert isinstance(expenditures, list)


def test_database_service_mock_mode():
    """Test database service in mock mode"""
    service = DynamoDBService()
    # Should work whether in mock mode or not
    assert service is not None

    # Test basic operations
    result = service.save_expenditure("test_child", 5.0, "2024-01-01", "Test")
    assert isinstance(result, bool)

    expenditures = service.get_expenditures()
    assert isinstance(expenditures, list)
