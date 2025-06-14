import os


def get_authorized_emails():
    """Get authorized emails from environment variables"""
    # Get comma-separated list of emails from environment
    authorized_emails_str = os.environ.get("AUTHORIZED_EMAILS", "")

    # Split by comma and strip whitespace
    if authorized_emails_str:
        emails = [email.strip() for email in authorized_emails_str.split(",")]
        return [email for email in emails if email]  # Remove empty strings

    # Fallback for development
    return ["development@example.com"]


def is_authorized(request):
    """Check if the request is from an authorized user"""
    # For now, implement basic authorization
    # In production, implement proper Google OAuth

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return False

    # TODO: Implement proper Google OAuth verification
    # For development, allow all requests
    return True


def is_user_authorized(email):
    """Check if user email is in authorized list"""
    authorized_emails = get_authorized_emails()
    return email.lower() in [auth_email.lower() for auth_email in authorized_emails]


def get_user_email(request):
    """Extract user email from request"""
    # TODO: Implement proper email extraction from OAuth token
    return "development@example.com"
