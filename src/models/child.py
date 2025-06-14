class Child:
    def __init__(self, name: str, total_earnings: float = 0.0):
        self.name = name
        self.total_earnings = total_earnings
        self.expenditures = []

    def add_expenditure(self, expenditure):
        """Add an expenditure to this child's record"""
        self.expenditures.append(expenditure)

    def get_total_spent(self) -> float:
        """Calculate total amount spent by this child"""
        return sum(exp.amount for exp in self.expenditures)

    def get_balance(self) -> float:
        """Calculate remaining balance"""
        return self.total_earnings - self.get_total_spent()

    def __repr__(self):
        return f"Child(name='{self.name}', total_earnings={self.total_earnings})"
