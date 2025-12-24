"""Authentication utilities for JWT, password hashing, and refresh tokens."""

import os
import time
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dateutil import tz


# JWT token expiration: 48 hours
ACCESS_TOKEN_EXPIRY_HOURS = 48
# Refresh token expiration: 48 hours
REFRESH_TOKEN_EXPIRY_HOURS = 48


def get_jwt_secret() -> str:
    """Get JWT secret from environment variable."""
    return os.environ.get('JWT_SECRET', 'default-secret-change-in-production')


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password: Plain text password
        password_hash: Hashed password string
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def generate_access_token(user_id: str) -> str:
    """
    Generate a JWT access token.
    
    Args:
        user_id: User ID to include in token
    
    Returns:
        JWT token string
    """
    secret = get_jwt_secret()
    expiration = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRY_HOURS)
    
    payload = {
        'user_id': user_id,
        'exp': expiration,
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    
    return jwt.encode(payload, secret, algorithm='HS256')


def generate_refresh_token() -> str:
    """
    Generate a refresh token (simple UUID-like string).
    
    Returns:
        Refresh token string
    """
    import uuid
    return str(uuid.uuid4())


def get_refresh_token_expiry() -> int:
    """
    Get refresh token expiry timestamp.
    
    Returns:
        Unix timestamp for refresh token expiry
    """
    expiry_time = datetime.utcnow() + timedelta(hours=REFRESH_TOKEN_EXPIRY_HOURS)
    return int(expiry_time.timestamp())


def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        secret = get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired.
    
    Args:
        token: JWT token string
    
    Returns:
        True if expired, False otherwise
    """
    try:
        secret = get_jwt_secret()
        jwt.decode(token, secret, algorithms=['HS256'], options={"verify_exp": False})
        # If decode succeeds, check expiration manually
        payload = jwt.decode(token, secret, algorithms=['HS256'], options={"verify_exp": False})
        exp = payload.get('exp')
        if exp:
            return time.time() > exp
        return True
    except Exception:
        return True


def extract_user_timezone(event: Dict[str, Any]) -> str:
    """
    Extract user timezone from request headers or JWT token.
    Defaults to UTC if not found.
    
    Args:
        event: Lambda event dictionary
    
    Returns:
        Timezone string (e.g., 'Asia/Kolkata', 'UTC')
    """
    # Try to get timezone from headers
    headers = event.get('headers', {}) or {}
    timezone = headers.get('X-User-Timezone') or headers.get('x-user-timezone')
    
    if timezone:
        # Validate timezone
        try:
            tz.gettz(timezone)
            return timezone
        except Exception:
            pass
    
    # Try to get from JWT token if available
    auth_header = headers.get('Authorization') or headers.get('authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')
        payload = validate_token(token)
        if payload and 'timezone' in payload:
            return payload['timezone']
    
    # Default to UTC
    return 'UTC'


def get_current_timestamp(timezone: str = 'UTC') -> int:
    """
    Get current timestamp in specified timezone.
    
    Args:
        timezone: Timezone string (default: UTC)
    
    Returns:
        Unix timestamp as integer
    """
    tz_obj = tz.gettz(timezone) or tz.UTC
    now = datetime.now(tz_obj)
    return int(now.timestamp())


def get_start_of_day_timestamp(timezone: str = 'UTC') -> int:
    """
    Get timestamp for start of current day in specified timezone.
    
    Args:
        timezone: Timezone string (default: UTC)
    
    Returns:
        Unix timestamp for start of day
    """
    tz_obj = tz.gettz(timezone) or tz.UTC
    now = datetime.now(tz_obj)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(start_of_day.timestamp())


def get_end_of_day_timestamp(timezone: str = 'UTC') -> int:
    """
    Get timestamp for end of current day in specified timezone.
    
    Args:
        timezone: Timezone string (default: UTC)
    
    Returns:
        Unix timestamp for end of day
    """
    tz_obj = tz.gettz(timezone) or tz.UTC
    now = datetime.now(tz_obj)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return int(end_of_day.timestamp())


def is_refresh_token_valid(refresh_token: str, stored_token: str, expiry_timestamp: int) -> bool:
    """
    Validate a refresh token.
    
    Args:
        refresh_token: Refresh token to validate
        stored_token: Stored refresh token from database
        expiry_timestamp: Expiry timestamp from database
    
    Returns:
        True if valid, False otherwise
    """
    # Check if tokens match
    if refresh_token != stored_token:
        return False
    
    # Check if token has expired
    current_timestamp = int(time.time())
    if current_timestamp > expiry_timestamp:
        return False
    
    return True

