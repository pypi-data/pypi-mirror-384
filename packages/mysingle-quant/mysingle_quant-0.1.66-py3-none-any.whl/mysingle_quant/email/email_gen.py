# path: app/utils/email_gen.py


import logging

from ..core.config import settings
from .email_sending import EmailData, render_email_template
from .email_token import generate_email_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def generate_verification_email(email_to: str, origin: str) -> EmailData:
    """
    신규 가입자 검증 이메일 발송 함수
    """
    project_name = settings.PROJECT_NAME
    verification_token = generate_email_token(email_to)

    verification_link = f"{origin}/api/auth/verify-email?token={verification_token}"

    subject = f"{project_name} - 이메일 인증 요청"
    html_content = render_email_template(
        template_name="verify_email.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "frontend_url": settings.FRONTEND_URL,
            "email": email_to,
            "link": verification_link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(
    email_to: str, email: str, token: str, origin: str
) -> EmailData:
    """
    패스워드 리셋 이메일 생성
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - 패스워드 재설정"
    link = f"{origin}/auth/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "frontend_url": settings.FRONTEND_URL,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str,
    username: str,
    password: str,
    origin: str,
) -> EmailData:
    """
    신규 계정 생성 이메일 생성(관리자)
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    link = f"{origin}/"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "frontend_url": settings.FRONTEND_URL,
            "username": username,
            "password": password,
            "email": email_to,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_confirmation_email(
    email_to: str, username: str, origin: str
) -> EmailData:
    """
    비밀번호 재설정 완료 알림 이메일 생성
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - 비밀번호 변경 완료"

    html_content = render_email_template(
        template_name="password_reset_confirmation.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "frontend_url": settings.FRONTEND_URL,
            "username": username,
            "email": email_to,
            "login_link": f"{origin}/auth/login",
            "support_email": settings.EMAILS_FROM_EMAIL,
        },
    )
    return EmailData(html_content=html_content, subject=subject)
