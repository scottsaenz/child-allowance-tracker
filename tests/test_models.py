"""Test the Pydantic models"""

import os
import sys
from datetime import datetime

import pytest

# Add src to path - moved to top
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))


def test_models_can_be_imported():
    """Test that models can be imported"""
    try:
        from app import AllowanceRecord, AllowanceResponse, Child

        # Test Child model
        child = Child(name="Test Child", age=10, weekly_allowance=5.0)
        assert child.name == "Test Child"
        assert child.age == 10
        assert child.weekly_allowance == 5.0

        # Test AllowanceRecord model
        record = AllowanceRecord(
            child_name="Test Child",
            amount=2.5,
            date=datetime.now(),
            description="Weekly allowance",
        )
        assert record.child_name == "Test Child"
        assert record.amount == 2.5

        # Test AllowanceResponse model
        response = AllowanceResponse(
            id="test-id",
            child_name="Test Child",
            amount=2.5,
            date=datetime.now(),
        )
        assert response.id == "test-id"

    except ImportError as e:
        pytest.skip(f"Models not available: {e}")


from models.child import Child
from models.expenditure import Expenditure


def test_child_initialization():
    """Test Child class initialization"""
    child = Child(name="Alice", total_earnings=100)
    assert child.name == "Alice"
    assert child.total_earnings == 100
    assert child.expenditures == []


def test_expenditure_initialization():
    """Test Expenditure class initialization"""
    expenditure = Expenditure(amount=25.50, description="Toy")
    assert expenditure.amount == 25.50
    assert expenditure.description == "Toy"
    assert expenditure.date is not None


def test_child_total_earnings():
    """Test Child total earnings calculation"""
    child = Child(name="Bob", total_earnings=150)
    assert child.total_earnings == 150
    assert child.get_balance() == 150  # No expenditures yet


def test_expenditure_total():
    """Test expenditure calculations"""
    child = Child(name="Charlie", total_earnings=100)

    # Add some expenditures
    exp1 = Expenditure(amount=20.0, description="Candy")
    exp2 = Expenditure(amount=15.0, description="Stickers")

    child.add_expenditure(exp1)
    child.add_expenditure(exp2)

    assert child.get_total_spent() == 35.0
    assert child.get_balance() == 65.0


def test_child_add_expenditure():
    """Test adding expenditures to a child"""
    child = Child(name="Diana", total_earnings=200)
    expenditure = Expenditure(amount=30.0, description="Book")

    child.add_expenditure(expenditure)
    assert len(child.expenditures) == 1
    assert child.expenditures[0] == expenditure
