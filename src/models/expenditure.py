from datetime import datetime


class Expenditure:
    def __init__(self, amount: float, description: str, date: str | None = None):
        self.amount = amount
        self.description = description
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.created_at = datetime.now()

    def __repr__(self):
        return f"Expenditure(amount={self.amount}, description='{self.description}', date='{self.date}')"
