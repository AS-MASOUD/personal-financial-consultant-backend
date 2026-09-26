from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import (
    AppException,
    AuthenticationException,
    EntityConflictException,
)
from src.app.core.security import create_access_token, hash_password, verify_password
from src.app.core.settings import get_settings
from src.app.database.models import AuditEntryModel, SystemRole, UserModel
from src.modules.auth.application.dtos import (
    ChangePasswordRequest,
    LoginWithOTPRequest,
    LoginWithPasswordRequest,
    OTPResponse,
    ProfileUpdateRequest,
    RequestOTPRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from src.modules.communications.application.otp_service import OTPService, normalize_identifier

settings = get_settings()


class AuthService:
    def __init__(self):
        self.otp_service = OTPService()

    async def register(self, db: AsyncSession, request: UserRegisterRequest) -> TokenResponse:
        # Validate that at least email or phone_number is provided
        if not request.email and not request.phone_number:
            raise AppException("لطفاً حداقل ایمیل یا شماره موبایل را وارد نمایید.", code="MISSING_CONTACT", status_code=400)

        # Check existing
        clean_email = request.email.strip().lower() if request.email else None
        clean_phone = None
        if request.phone_number:
            clean_phone, _ = normalize_identifier(request.phone_number)

        conditions = []
        if clean_email:
            conditions.append(UserModel.email == clean_email)
        if clean_phone:
            conditions.append(UserModel.phone_number == clean_phone)

        if conditions:
            stmt_exist = select(UserModel).where(or_(*conditions))
            res_exist = await db.execute(stmt_exist)
            if res_exist.scalar_one_or_none() is not None:
                raise EntityConflictException("کاربری با این ایمیل یا شماره موبایل در سامانه ثبت شده است.")

        # Determine role: First user is sysmanager, subsequent users are user
        stmt_count = select(func.count(UserModel.id))
        user_count = (await db.execute(stmt_count)).scalar() or 0
        role = SystemRole.SYSMANAGER.value if user_count == 0 else SystemRole.USER.value

        hashed = hash_password(request.password) if request.password else None
        now = datetime.now(UTC)

        user = UserModel(
            email=clean_email,
            phone_number=clean_phone,
            hashed_password=hashed,
            full_name=request.full_name,
            role=role,
            is_active=True,
            is_verified=True,
            last_login_at=now,
        )
        db.add(user)
        await db.flush()

        audit = AuditEntryModel(
            action="USER_REGISTER",
            entity_type="USER",
            entity_id=str(user.id),
            details={
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "is_first_user": user_count == 0,
            },
        )
        db.add(audit)
        await db.flush()

        token_data = {
            "sub": str(user.id),
            "email": user.email or "",
            "phone_number": user.phone_number or "",
            "role": user.role,
        }
        access_token = create_access_token(token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    async def login_with_password(
        self, db: AsyncSession, request: LoginWithPasswordRequest
    ) -> TokenResponse:
        clean_id, channel = normalize_identifier(request.identifier)

        if channel == "email":
            stmt = select(UserModel).where(UserModel.email == clean_id)
        else:
            stmt = select(UserModel).where(UserModel.phone_number == clean_id)

        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if user is None:
            raise AppException(
                "حساب کاربری با این مشخصات یافت نشد. لطفاً ابتدا ثبت‌نام فرمایید.",
                code="USER_NOT_FOUND",
                status_code=404,
            )

        if not user.hashed_password:
            raise AuthenticationException(
                "این حساب فاقد رمز عبور ثابت است. لطفاً از طریق ورود با کد یکبار مصرف (OTP) وارد شوید."
            )

        if not verify_password(request.password, user.hashed_password):
            raise AuthenticationException("رمز عبور وارد شده نادرست است.")

        if not user.is_active:
            raise AuthenticationException(
                "حساب کاربری شما غیرفعال شده است. لطفاً با مدیر سیستم تماس بگیرید."
            )

        user.last_login_at = datetime.now(UTC)
        await db.flush()

        audit = AuditEntryModel(
            action="USER_LOGIN_PASSWORD",
            entity_type="USER",
            entity_id=str(user.id),
            details={"identifier": clean_id, "channel": channel},
        )
        db.add(audit)
        await db.flush()

        token_data = {
            "sub": str(user.id),
            "email": user.email or "",
            "phone_number": user.phone_number or "",
            "role": user.role,
        }
        access_token = create_access_token(token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    async def login(self, db: AsyncSession, request: UserLoginRequest) -> TokenResponse:
        """Legacy and universal login method."""
        identifier = request.identifier or request.email
        if not identifier:
            raise AppException("لطفاً ایمیل یا شماره موبایل را وارد نمایید.", code="MISSING_IDENTIFIER", status_code=400)
        return await self.login_with_password(
            db=db,
            request=LoginWithPasswordRequest(identifier=identifier, password=request.password),
        )

    async def request_login_otp(
        self, db: AsyncSession, request: RequestOTPRequest
    ) -> OTPResponse:
        clean_id, channel = normalize_identifier(request.identifier)

        # Ensure user exists for login OTP
        if channel == "email":
            stmt = select(UserModel).where(UserModel.email == clean_id)
        else:
            stmt = select(UserModel).where(UserModel.phone_number == clean_id)

        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if user is None:
            raise AppException(
                "حساب کاربری با این مشخصات یافت نشد. لطفاً ابتدا ثبت‌نام فرمایید.",
                code="USER_NOT_FOUND",
                status_code=404,
            )

        if not user.is_active:
            raise AuthenticationException(
                "حساب کاربری شما غیرفعال شده است. لطفاً با مدیر سیستم تماس بگیرید."
            )

        data = await self.otp_service.request_otp(
            db=db,
            identifier=request.identifier,
            purpose="login",
        )
        return OTPResponse(
            identifier=str(data["identifier"]),
            channel=str(data["channel"]),
            expires_in=int(data["expires_in"] or 120),
            cooldown_seconds=int(data["cooldown_seconds"] or 60),
            debug_code=str(data["debug_code"]) if data.get("debug_code") else None,
            message="کد یکبار مصرف با موفقیت ارسال شد.",
        )

    async def login_with_otp(
        self, db: AsyncSession, request: LoginWithOTPRequest
    ) -> TokenResponse:
        # Verify OTP code first
        await self.otp_service.verify_otp(
            db=db,
            identifier=request.identifier,
            code=request.code,
            purpose="login",
        )

        clean_id, channel = normalize_identifier(request.identifier)

        if channel == "email":
            stmt = select(UserModel).where(UserModel.email == clean_id)
        else:
            stmt = select(UserModel).where(UserModel.phone_number == clean_id)

        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if user is None:
            raise AppException(
                "حساب کاربری با این مشخصات یافت نشد. لطفاً ابتدا ثبت‌نام فرمایید.",
                code="USER_NOT_FOUND",
                status_code=404,
            )

        if not user.is_active:
            raise AuthenticationException("حساب کاربری شما غیرفعال شده است. لطفاً با مدیر سیستم تماس بگیرید.")

        now = datetime.now(UTC)
        user.last_login_at = now
        audit = AuditEntryModel(
            action="USER_LOGIN_OTP",
            entity_type="USER",
            entity_id=str(user.id),
            details={"identifier": clean_id, "channel": channel},
        )
        db.add(audit)
        await db.flush()

        token_data = {
            "sub": str(user.id),
            "email": user.email or "",
            "phone_number": user.phone_number or "",
            "role": user.role,
        }
        access_token = create_access_token(token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    async def change_password(
        self, db: AsyncSession, user: UserModel, request: ChangePasswordRequest
    ) -> None:
        if user.hashed_password and not verify_password(request.old_password, user.hashed_password):
            raise AuthenticationException("Current password is incorrect.")

        user.hashed_password = hash_password(request.new_password)
        await db.flush()

        audit = AuditEntryModel(
            action="USER_PASSWORD_CHANGE",
            entity_type="USER",
            entity_id=str(user.id),
            details={"email": user.email, "phone_number": user.phone_number},
        )
        db.add(audit)
        await db.flush()

    async def update_profile(
        self, db: AsyncSession, user: UserModel, request: ProfileUpdateRequest
    ) -> UserResponse:
        # Check email uniqueness if changing email
        if request.email is not None:
            clean_email = request.email.strip().lower() if request.email.strip() else None
            if clean_email and clean_email != user.email:
                stmt = select(UserModel).where(UserModel.email == clean_email, UserModel.id != user.id)
                res = await db.execute(stmt)
                if res.scalar_one_or_none() is not None:
                    raise EntityConflictException("این آدرس ایمیل قبلاً توسط کاربر دیگری ثبت شده است.")
            user.email = clean_email

        # Check phone number uniqueness if changing phone
        if request.phone_number is not None:
            clean_phone = None
            if request.phone_number.strip():
                clean_phone, _ = normalize_identifier(request.phone_number)
            if clean_phone and clean_phone != user.phone_number:
                stmt = select(UserModel).where(UserModel.phone_number == clean_phone, UserModel.id != user.id)
                res = await db.execute(stmt)
                if res.scalar_one_or_none() is not None:
                    raise EntityConflictException("این شماره موبایل قبلاً توسط کاربر دیگری ثبت شده است.")
            user.phone_number = clean_phone

        if request.full_name is not None and request.full_name.strip():
            user.full_name = request.full_name.strip()

        if request.age is not None:
            user.age = request.age

        if request.job is not None:
            user.job = request.job.strip() if request.job.strip() else None

        if request.bio is not None:
            user.bio = request.bio.strip() if request.bio.strip() else None

        await db.flush()

        audit = AuditEntryModel(
            action="USER_PROFILE_UPDATE",
            entity_type="USER",
            entity_id=str(user.id),
            details={
                "email": user.email,
                "phone_number": user.phone_number,
                "full_name": user.full_name,
                "age": user.age,
                "job": user.job,
            },
        )
        db.add(audit)
        await db.flush()

        return UserResponse.model_validate(user)
