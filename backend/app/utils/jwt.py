from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"JWT decode error: {type(e).__name__}: {str(e)}")
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """Extract user ID from JWT token"""
    payload = decode_access_token(token)
    if payload:
        user_id = payload.get("sub")  # 'sub' is the standard JWT claim for subject (user ID)
        return int(user_id) if user_id else None
    return None

