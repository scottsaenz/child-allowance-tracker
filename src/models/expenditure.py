class Expenditure:
    def __init__(self, amount, date, description):
        self.amount = amount
        self.date = date
        self.description = description

    def __repr__(self):
        return f"Expenditure(amount={self.amount}, date={self.date}, description='{self.description}')"