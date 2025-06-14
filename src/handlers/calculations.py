def calculate_totals(earnings, expenditures):
    total_earned = sum(earnings)
    total_spent = sum(expenditures)
    return total_earned, total_spent

def get_child_financials(child_data):
    financials = {}
    for child in child_data:
        earnings = child.get('earnings', [])
        expenditures = child.get('expenditures', [])
        total_earned, total_spent = calculate_totals(earnings, expenditures)
        financials[child['name']] = {
            'total_earned': total_earned,
            'total_spent': total_spent,
            'balance': total_earned - total_spent
        }
    return financials