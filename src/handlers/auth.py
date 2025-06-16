"""Authentication module with Google OAuth integration"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "https://xt7m8ql2y6.execute-api.us-east-1.amazonaws.com/auth/callback",
)


# Models
@dataclass
class User:
    """User model for authentication"""

    email: str
    name: str
    google_id: str
    picture: str | None = None
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime | None = None

    def __post_init__(self):
        """Set created_at if not provided"""
        if self.created_at is None:
            self.created_at = datetime.now()


class TokenData(BaseModel):
    email: str | None = None
    google_id: str | None = None


# Global users database - make sure this is clearly defined
users_db: dict[str, User] = {}

# OAuth setup
oauth = OAuth()


def setup_oauth():
    """Setup OAuth configuration"""
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        oauth.register(
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid_configuration",
            client_kwargs={
                "scope": "openid email profile https://www.googleapis.com/auth/spreadsheets"
            },
        )
        logger.info("Google OAuth configured successfully")
    else:
        logger.warning("Google OAuth not configured - missing client credentials")


# JWT Functions
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData | None:
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        google_id: str = payload.get("google_id")

        if email is None or google_id is None:
            logger.error("Token missing required claims")
            raise HTTPException(
                status_code=401, detail="Invalid token: missing required claims"
            )

        token_data = TokenData(email=email, google_id=google_id)
        return token_data

    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token") from e


# User management
def get_user_by_email(email: str) -> User | None:
    """Get user by email from database"""
    return users_db.get(email)


def create_user(user_info: dict) -> User:
    """Create new user from Google OAuth info"""
    user = User(
        email=user_info["email"],
        name=user_info["name"],
        picture=user_info.get("picture"),
        google_id=user_info["sub"],
        created_at=datetime.utcnow(),
    )
    users_db[user.email] = user
    logger.info(f"Created new user: {user.email}")
    return user


def get_or_create_user(user_info: dict) -> User:
    """Get existing user or create new one from OAuth user info"""
    global users_db

    email = user_info.get("email")

    if not email:
        raise ValueError("User info must contain email")

    # Debug: Check database state before
    logger.info(f"Before check - users_db id: {id(users_db)}, length: {len(users_db)}")

    # Check if user already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        logger.info(f"Found existing user: {email}")
        return existing_user

    # Create new user
    user = User(
        email=email,
        name=user_info.get("name", ""),
        google_id=user_info.get("sub", ""),
        picture=user_info.get("picture"),
        is_active=True,
        is_admin=False,
    )

    # Store user in database
    logger.info(f"Storing user {email} in users_db (id: {id(users_db)})")
    users_db[email] = user
    logger.info(
        f"After storage - users_db length: {len(users_db)}, keys: {list(users_db.keys())}"
    )
    logger.info(f"Created new user: {email}")

    return user


# Authentication dependencies
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get current authenticated user"""
    token_data = verify_token(credentials.credentials)
    user = get_user_by_email(token_data.email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Optional authentication (for public endpoints that can benefit from user context)
async def get_current_user_optional(request: Request) -> User | None:
    """Get current user from token, return None if not authenticated"""
    try:
        authorization: str = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None

        token = authorization.split(" ")[1]
        token_data = verify_token(token)

        if not token_data:
            return None

        user = get_user_by_email(token_data.email)
        return user if user and user.is_active else None
    except Exception:
        return None


# Keep your existing functions for backward compatibility
def get_authorized_emails():
    """Get authorized emails from environment variables"""
    authorized_emails_str = os.environ.get("AUTHORIZED_EMAILS", "")
    if authorized_emails_str:
        emails = [email.strip() for email in authorized_emails_str.split(",")]
        return [email for email in emails if email]
    return ["development@example.com"]


def is_authorized(request):
    """Legacy authorization check - use get_current_user instead"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return False
    return True


def is_user_authorized(email):
    """Check if user email is in authorized list"""
    authorized_emails = get_authorized_emails()
    return email.lower() in [auth_email.lower() for auth_email in authorized_emails]


def get_user_email(request):
    """Legacy email extraction - use get_current_user instead"""
    return "development@example.com"


# Admin check
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")


async def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Ensure current user is admin"""
    if current_user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# Initialize OAuth
setup_oauth()
