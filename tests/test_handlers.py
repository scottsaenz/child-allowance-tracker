import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from handlers.calculations import calculate_totals
from handlers.expenditures import get_expenditures, post_expenditure


def test_post_expenditure():
    """Test posting expenditure (mock)"""
    result = post_expenditure("child1", 5.00, "2024-06-25", "Test expense")
    assert isinstance(result, bool)


def test_get_expenditures():
    """Test getting expenditures"""
    expenditures = get_expenditures()
    assert isinstance(expenditures, list)


def test_calculate_totals():
    """Test calculating totals"""
    totals = calculate_totals()
    assert isinstance(totals, dict)
