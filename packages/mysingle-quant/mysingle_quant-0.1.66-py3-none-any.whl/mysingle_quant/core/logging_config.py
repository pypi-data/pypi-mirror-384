"""
로깅 설정 모듈
"""

import logging
import sys
from pathlib import Path

try:
    import colorlog

    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logging():
    """애플리케이션 로깅 설정"""

    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 컬러 로그 포맷 (colorlog 사용)
    if HAS_COLORLOG:
        color_format = (
            "%(log_color)s%(asctime)s%(reset)s | "
            "%(log_color)s%(levelname)-8s%(reset)s | "
            "%(cyan)s%(name)-30s%(reset)s | "
            "%(message_log_color)s%(message)s%(reset)s"
        )
        date_format = "%H:%M:%S"

        console_formatter = colorlog.ColoredFormatter(
            color_format,
            datefmt=date_format,
            log_colors={
                "DEBUG": "blue",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={
                "message": {
                    "DEBUG": "white",
                    "INFO": "white",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red",
                }
            },
        )
    else:
        # colorlog 없을 때 기본 포맷
        log_format = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
        date_format = "%H:%M:%S"
        console_formatter = logging.Formatter(log_format, datefmt=date_format)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 파일 핸들러 (일반 로그) - 컬러 없이
    file_format = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
    file_date_format = "%Y-%m-%d %H:%M:%S"

    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(file_format, datefmt=file_date_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # 에러 로그 파일 핸들러
    error_handler = logging.FileHandler(log_dir / "error.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(file_format, datefmt=file_date_format)
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)

    # 이메일 관련 로거 설정
    email_logger = logging.getLogger("app.utils.email")
    email_logger.setLevel(logging.INFO)

    # 유저 관리 로거 설정
    user_logger = logging.getLogger("app.services.user_manager")
    user_logger.setLevel(logging.INFO)

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)
    logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
    logging.getLogger("pymongo.command").setLevel(logging.WARNING)
    logging.getLogger("pymongo.topology").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스를 가져오는 헬퍼 함수"""
    return logging.getLogger(name)
