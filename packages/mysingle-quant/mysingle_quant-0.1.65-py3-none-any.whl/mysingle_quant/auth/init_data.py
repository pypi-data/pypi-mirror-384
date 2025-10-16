import logging

from ..core.config import settings
from .models import User
from .security.password import PasswordHelper

password_helper = PasswordHelper()

logger = logging.getLogger(__name__)


async def create_first_super_admin() -> None:
    """첫 번째 Super Admin 사용자 생성"""
    try:
        logger.info("Checking for existing Super Admin user...")

        # 설정 값 확인
        if (
            settings.SUPERUSER_EMAIL == "your_email@example.com"
            or settings.SUPERUSER_PASSWORD == "change-this-admin-password"
        ):
            logger.warning(
                "Super Admin creation skipped: Default email/password values detected. "
                "Please set SUPERUSER_EMAIL and SUPERUSER_PASSWORD environment variables."
            )
            return

        logger.info(f"Creating Super Admin with email: {settings.SUPERUSER_EMAIL}")

        # 기존 Super Admin 사용자 확인 (이메일 기준)
        existing_super_admin = await User.find_one({"email": settings.SUPERUSER_EMAIL})
        if existing_super_admin:
            logger.info(
                f"✅ Super Admin user already exists: {existing_super_admin.email}"
            )
            return

        # Super Admin User 생성
        logger.info("Creating new Super Admin user...")
        user = User(
            email=settings.SUPERUSER_EMAIL,
            hashed_password=password_helper.hash(settings.SUPERUSER_PASSWORD),
            full_name=settings.SUPERUSER_FULLNAME,
            is_active=True,
            is_superuser=True,
            is_verified=True,
        )

        await user.save()
        logger.info(f"✅ Super Admin user created: {user.full_name} ({user.email})")

        logger.info(
            f"✅ First Super Admin created successfully: {settings.SUPERUSER_EMAIL}"
        )

    except Exception as e:
        logger.error(
            f"❌ Failed to create first Super Admin: {type(e).__name__}: {str(e)}"
        )
        logger.error(f"Settings - Email: {settings.SUPERUSER_EMAIL}")
        logger.error(f"Settings - Fullname: {settings.SUPERUSER_FULLNAME}")
        # Super Admin 생성 실패가 애플리케이션 시작을 막지 않도록 함
        # raise e  # 주석 처리하여 애플리케이션이 계속 시작되도록 함
