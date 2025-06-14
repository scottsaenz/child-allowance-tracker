def validate_expenditure(amount, date, description):
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("Amount must be a positive number.")
    
    if not isinstance(date, str) or not date:
        raise ValueError("Date must be a non-empty string.")
    
    if not isinstance(description, str) or not description:
        raise ValueError("Description must be a non-empty string.")
    
    return True

def validate_user_input(user_input, allowed_values):
    if user_input not in allowed_values:
        raise ValueError(f"Input must be one of the following: {allowed_values}")
    
    return True