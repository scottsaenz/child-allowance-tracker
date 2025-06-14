import unittest
from src.handlers.calculations import calculate_totals
from src.handlers.expenditures import post_expenditure
from src.models.child import Child
from src.models.expenditure import Expenditure

class TestHandlers(unittest.TestCase):

    def setUp(self):
        self.child = Child(name="John Doe", total_earnings=1000)
        self.expenditure = Expenditure(amount=200, date="2023-01-01", description="Toys")

    def test_calculate_totals(self):
        earnings = self.child.total_earnings
        expenditures = [self.expenditure.amount]
        total_spent = sum(expenditures)
        total_remaining = calculate_totals(earnings, total_spent)
        self.assertEqual(total_remaining, 800)

    def test_post_expenditure(self):
        response = post_expenditure(self.expenditure)
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], "Expenditure posted successfully.")

if __name__ == '__main__':
    unittest.main()