from src.models.child import Child
from src.models.expenditure import Expenditure

def test_child_initialization():
    child = Child(name="Alice", total_earnings=100)
    assert child.name == "Alice"
    assert child.total_earnings == 100

def test_expenditure_initialization():
    expenditure = Expenditure(amount=20, date="2023-01-01", description="Toys")
    assert expenditure.amount == 20
    assert expenditure.date == "2023-01-01"
    assert expenditure.description == "Toys"

def test_child_total_earnings():
    child = Child(name="Bob", total_earnings=150)
    assert child.total_earnings == 150

def test_expenditure_total():
    expenditures = [
        Expenditure(amount=10, date="2023-01-01", description="Snacks"),
        Expenditure(amount=15, date="2023-01-02", description="Books"),
    ]
    total_spent = sum(exp.amount for exp in expenditures)
    assert total_spent == 25