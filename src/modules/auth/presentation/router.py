from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.security import create_access_token
from src.app.core.settings import get_settings
from src.app.database.models import UserModel
from src.app.database.session import get_db_session
from src.modules.auth.application.dtos import (
    ChangePasswordRequest,
    FinancialOnboardingRequest,
    FinancialOnboardingResponse,
    JobBenchmarkResponse,
    LoginWithOTPRequest,
    OTPResponse,
    ProfileUpdateRequest,
    RegisterRequestOTP,
    RegisterVerifyOTPRequest,
    RequestOTPRequest,
    RiskAssessmentRequest,
    RiskOnboardingResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from src.modules.auth.application.services import AuthService
from src.modules.auth.presentation.dependencies import get_current_user

settings = get_settings()
auth_router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])
auth_service = AuthService()


@auth_router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Register a new user. If no users currently exist, the first user is granted 'sysmanager' role."""
    return await auth_service.register(db=db, request=request)


@auth_router.post(
    "/register/otp/request",
    response_model=OTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Request OTP verification code for new user registration",
)
async def request_register_otp(
    request: RegisterRequestOTP,
    db: AsyncSession = Depends(get_db_session),
) -> OTPResponse:
    """Validate user registration data and send OTP code to mobile phone."""
    return await auth_service.request_register_otp(db=db, request=request)


@auth_router.post(
    "/register/otp/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Verify OTP code and create new registered user",
)
async def verify_register_otp(
    request: RegisterVerifyOTPRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Verify received OTP code and finalize user registration."""
    return await auth_service.register_with_otp(db=db, request=request)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with static password",
)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate with either email or Iranian mobile phone number and static password."""
    return await auth_service.login(db=db, request=request)


@auth_router.post(
    "/otp/request",
    response_model=OTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Request OTP verification code for mobile or email",
)
async def request_otp(
    request: RequestOTPRequest,
    db: AsyncSession = Depends(get_db_session),
) -> OTPResponse:
    """Send a temporary OTP code to an Iranian phone number via SMS or to an email address."""
    return await auth_service.request_login_otp(db=db, request=request)


@auth_router.post(
    "/otp/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP code and authenticate / auto-register",
)
async def verify_otp(
    request: LoginWithOTPRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Verify received OTP code. If user does not exist, an account is automatically provisioned."""
    return await auth_service.login_with_otp(db=db, request=request)


@auth_router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: UserModel = Depends(get_current_user),
) -> UserResponse:
    """Retrieve profile and role information of current logged-in user."""
    return UserResponse.model_validate(current_user)


@auth_router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current authenticated user profile",
)
async def update_me(
    request: ProfileUpdateRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Update profile details (name, email, phone, age, job, bio) of current logged-in user."""
    return await auth_service.update_profile(db=db, user=current_user, request=request)


@auth_router.post(
    "/onboarding/financial",
    response_model=FinancialOnboardingResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit user financial onboarding information and receive job salary benchmark",
)
async def submit_financial_onboarding(
    request: FinancialOnboardingRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FinancialOnboardingResponse:
    """Save user financial figures (income, assets, debt, goals) and calculate job salary benchmark."""
    return await auth_service.submit_financial_onboarding(db=db, user=current_user, request=request)


@auth_router.get(
    "/benchmark",
    response_model=JobBenchmarkResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate industry salary benchmark for a job",
)
async def get_job_benchmark(
    job: str,
    salary: Decimal,
) -> JobBenchmarkResponse:
    """Query average salary, bounds, and recommendations for a specific job title."""
    return auth_service.calculate_job_benchmark(job=job, user_salary=salary)


@auth_router.post(
    "/onboarding/risk",
    response_model=RiskOnboardingResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit psychological risk assessment answers and receive portfolio allocation suggestion",
)
async def submit_risk_onboarding(
    request: RiskAssessmentRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RiskOnboardingResponse:
    """Evaluate financial psychological questions, compute risk score and portfolio allocation suggestion."""
    return await auth_service.submit_risk_onboarding(db=db, user=current_user, request=request)


@auth_router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password for current user",
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """Update password for the current user after validating old password."""
    await auth_service.change_password(db=db, user=current_user, request=request)
    return {"message": "Password changed successfully."}


@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    current_user: UserModel = Depends(get_current_user),
) -> TokenResponse:
    """Issue a fresh JWT token for currently active user session."""
    token_data = {
        "sub": str(current_user.id),
        "email": current_user.email or "",
        "phone_number": current_user.phone_number or "",
        "role": current_user.role,
    }
    new_token = create_access_token(token_data)
    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(current_user),
    )
