from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.user import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
    auto_error=False
)


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """Retrieves authenticated citizen if token present, else None."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
        email: str = payload.get("sub")
        if email is None:
            return None
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception:
        return None


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Validates the JWT token and retrieves the current authenticated citizen/user.
    Raises 401 if missing or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verifies that the current user has superuser privileges."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have sufficient privileges",
        )
    return current_user
