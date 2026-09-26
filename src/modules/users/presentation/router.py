import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.models import SystemRole, UserModel
from src.app.database.session import get_db_session
from src.modules.auth.application.dtos import UserResponse
from src.modules.auth.presentation.dependencies import get_current_user, require_roles
from src.modules.users.application.dtos import (
    RoleDefinitionResponse,
    UserCreateRequest,
    UserListResponse,
    UserUpdateRequest,
    UserUpdateRoleRequest,
    UserUpdateStatusRequest,
)
from src.modules.users.application.services import UserService

users_router = APIRouter(prefix="/users", tags=["System Role & User Management"])
user_service = UserService()


@users_router.get(
    "/roles",
    response_model=list[RoleDefinitionResponse],
    status_code=status.HTTP_200_OK,
    summary="List all available system roles and permissions",
)
async def list_roles() -> list[RoleDefinitionResponse]:
    """Retrieve definitions, descriptions, badges, and capability matrices for all supported roles."""
    return user_service.get_system_roles()


@users_router.get(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List system users with filters and search",
)
async def list_users(
    search: str | None = Query(None, description="Search by name or email"),
    role: str | None = Query(None, description="Filter by system role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_roles(SystemRole.SYSMANAGER, SystemRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> UserListResponse:
    """List users registered in the system. Accessible by SysManager and Financial Admin."""
    return await user_service.list_users(
        db=db,
        search=search,
        role=role,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@users_router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user with designated role (SysManager only)",
)
async def create_user(
    request: UserCreateRequest,
    current_user: UserModel = Depends(require_roles(SystemRole.SYSMANAGER)),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Create a new user directly with assigned system role (e.g. sysmanager, admin, user, viewer)."""
    user = await user_service.create_user(db=db, admin_user=current_user, request=request)
    return UserResponse.model_validate(user)


@users_router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user details by ID",
)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Get single user profile. Accessible by SysManager, Admin, or the user themselves."""
    if (
        current_user.role not in (SystemRole.SYSMANAGER.value, SystemRole.ADMIN.value)
        and current_user.id != user_id
    ):
        from src.app.core.exceptions import PermissionDeniedException

        raise PermissionDeniedException("Cannot view profile of other users.")

    user = await user_service.get_user_by_id(db=db, user_id=user_id)
    return UserResponse.model_validate(user)


@users_router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Change user role (SysManager only)",
)
async def update_user_role(
    user_id: uuid.UUID,
    request: UserUpdateRoleRequest,
    current_user: UserModel = Depends(require_roles(SystemRole.SYSMANAGER)),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Update role for a user (e.g. promote to sysmanager or admin). Protected against demoting last sysmanager."""
    user = await user_service.update_user_role(
        db=db, admin_user=current_user, user_id=user_id, new_role=request.role
    )
    return UserResponse.model_validate(user)


@users_router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate or deactivate user account (SysManager only)",
)
async def update_user_status(
    user_id: uuid.UUID,
    request: UserUpdateStatusRequest,
    current_user: UserModel = Depends(require_roles(SystemRole.SYSMANAGER)),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Enable or disable access for a user. Protected against deactivating self or last active sysmanager."""
    user = await user_service.update_user_status(
        db=db, admin_user=current_user, user_id=user_id, is_active=request.is_active
    )
    return UserResponse.model_validate(user)


@users_router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user details, role, or reset password (SysManager only)",
)
async def update_user(
    user_id: uuid.UUID,
    request: UserUpdateRequest,
    current_user: UserModel = Depends(require_roles(SystemRole.SYSMANAGER)),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Comprehensive user update including profile, role, status, and password reset."""
    user = await user_service.update_user(
        db=db, admin_user=current_user, user_id=user_id, request=request
    )
    return UserResponse.model_validate(user)


@users_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account (SysManager only)",
)
async def delete_user(
    user_id: uuid.UUID,
    current_user: UserModel = Depends(require_roles(SystemRole.SYSMANAGER)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Permanently delete user account. Protected against deleting self or last active sysmanager."""
    await user_service.delete_user(db=db, admin_user=current_user, user_id=user_id)
