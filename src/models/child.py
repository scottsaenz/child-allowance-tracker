class Child:
    def __init__(self, name):
        self.name = name
        self.total_earned = 0.0

    def add_earnings(self, amount):
        self.total_earned += amount

    def get_total_earned(self):
        return self.total_earned

    def __str__(self):
        return f"Child(name={self.name}, total_earned={self.total_earned})"