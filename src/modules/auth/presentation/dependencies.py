import uuid
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import AuthenticationException, PermissionDeniedException
from src.app.core.security import decode_access_token
from src.app.database.models import SystemRole, UserModel
from src.app.database.session import get_db_session

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> UserModel:
    if auth is None:
        raise AuthenticationException("Authentication required. Please log in.")

    payload = decode_access_token(auth.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Invalid authentication credentials.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError) as e:
        raise AuthenticationException("Invalid user identifier in token.") from e

    stmt = select(UserModel).where(UserModel.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationException("User account not found.")

    if not user.is_active:
        raise AuthenticationException("User account is deactivated.")

    return user


async def get_optional_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> UserModel | None:
    if auth is None:
        return None
    try:
        return await get_current_user(auth=auth, db=db)
    except Exception:
        return None


def require_roles(*allowed_roles: SystemRole | str) -> Callable:
    """Dependency factory that checks if current user belongs to one of allowed roles."""
    expected_values = {
        role.value if isinstance(role, SystemRole) else str(role) for role in allowed_roles
    }

    async def role_checker(
        current_user: UserModel = Depends(get_current_user),
    ) -> UserModel:
        if current_user.role not in expected_values:
            raise PermissionDeniedException(
                f"Access denied. User role '{current_user.role}' lacks sufficient privileges. "
                f"Required: {', '.join(sorted(expected_values))}"
            )
        return current_user

    return role_checker
