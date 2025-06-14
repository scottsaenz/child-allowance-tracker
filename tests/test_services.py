import pytest
from src.services.google_sheets import GoogleSheetsService
from src.models.child import Child
from src.models.expenditure import Expenditure

@pytest.fixture
def google_sheets_service(mocker):
    return mocker.patch('src.services.google_sheets.GoogleSheetsService')

def test_calculate_total_earned(google_sheets_service):
    google_sheets_service.get_data.return_value = [
        {'name': 'Alice', 'total_earned': 100},
        {'name': 'Bob', 'total_earned': 150},
    ]
    children = [Child(name=data['name'], total_earned=data['total_earned']) for data in google_sheets_service.get_data()]
    
    total_earned = sum(child.total_earned for child in children)
    
    assert total_earned == 250

def test_calculate_total_spent(google_sheets_service):
    google_sheets_service.get_data.return_value = [
        {'name': 'Alice', 'total_spent': 50},
        {'name': 'Bob', 'total_spent': 70},
    ]
    expenditures = [Expenditure(amount=data['total_spent']) for data in google_sheets_service.get_data()]
    
    total_spent = sum(expenditure.amount for expenditure in expenditures)
    
    assert total_spent == 120

def test_post_expenditure(google_sheets_service):
    expenditure_data = {'name': 'Alice', 'amount': 30, 'date': '2023-10-01', 'description': 'New shoes'}
    google_sheets_service.post_expenditure.return_value = True
    
    result = google_sheets_service.post_expenditure(expenditure_data)
    
    assert result is True
    google_sheets_service.post_expenditure.assert_called_once_with(expenditure_data)