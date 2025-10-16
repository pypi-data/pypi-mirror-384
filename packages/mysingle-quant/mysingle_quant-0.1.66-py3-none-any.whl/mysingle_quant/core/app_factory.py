"""FastAPI application factory with common middleware and configurations."""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass

from beanie import Document
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from ..auth.exception_handlers import register_auth_exception_handlers
from ..auth.init_data import create_first_super_admin
from ..auth.models import OAuthAccount, User
from ..health import create_health_router
from ..metrics import create_metrics_middleware
from .config import settings
from .db import init_mongo
from .logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    """Generate unique ID for each route based on its tags and name."""
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"


@dataclass
class AppConfig:
    """Configuration for FastAPI application creation."""

    service_name: str
    service_version: str = "1.0.0"
    environment: str = "development"
    description: str | None = None
    # Database
    enable_database: bool = True
    document_models: list[type[Document]] | None = None
    database_name: str | None = None
    # Security
    enable_auth: bool = False
    enable_oauth: bool = False
    public_paths: list[str] | None = None
    # CORS
    cors_origins: list[str] | None = None
    # Features
    enable_metrics: bool = True
    enable_health_check: bool = True
    # Lifespan
    lifespan: Callable | None = None


def create_lifespan(config: AppConfig) -> Callable:
    """Create lifespan context manager for the application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        # Startup
        startup_tasks = []

        # Initialize database if enabled
        if config.enable_database and config.document_models:
            if config.enable_auth:
                # Ensure auth models are included
                auth_models = [User, OAuthAccount]
                for model in auth_models:
                    if model not in config.document_models:
                        config.document_models.append(model)
            try:
                client = await init_mongo(
                    config.document_models,
                    config.service_name,
                )
                startup_tasks.append(("mongodb_client", client))
                logger.info(f"✅ Connected to MongoDB for {config.service_name}")

                # Create first super admin after database initialization
                await create_first_super_admin()

            except Exception as e:
                logger.error(f"❌ Failed to connect to MongoDB: {e}")
                if not settings.MOCK_DATABASE:
                    raise
                logger.warning("🔄 Running with mock database")

        # Store startup tasks in app state
        app.state.startup_tasks = startup_tasks

        # Run custom lifespan if provided
        if config.lifespan:
            async with config.lifespan(app):
                yield
        else:
            yield

        # Shutdown
        for task_name, task_obj in startup_tasks:
            if task_name == "mongodb_client":
                try:
                    task_obj.close()
                    logger.info("✅ Disconnected from MongoDB")
                except Exception as e:
                    logger.error(f"⚠️ Error disconnecting from MongoDB: {e}")

    return lifespan


def create_fastapi_app(
    service_name: str,
    service_version: str = "1.0.0",
    description: str | None = None,
    enable_database: bool = True,
    document_models: list[type[Document]] | None = None,
    database_name: str | None = None,
    enable_auth: bool = False,
    enable_oauth: bool = False,
    public_paths: list[str] | None = None,
    cors_origins: list[str] | None = None,
    enable_metrics: bool = True,
    enable_health_check: bool = True,
    lifespan: Callable | None = None,
) -> FastAPI:
    """Create a standardized FastAPI application.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        title: Custom title for the API documentation
        description: Custom description for the API
        enable_database: Whether to enable database initialization
        document_models: List of Beanie document models
        database_name: Custom database name (defaults to service_name)
        enable_auth: Whether to enable authentication middleware
        public_paths: List of public paths that don't require authentication
        cors_origins: List of allowed CORS origins
        enable_metrics: Whether to enable metrics middleware
        enable_health_check: Whether to include health check endpoints
        lifespan: Custom lifespan context manager

    Returns:
        Configured FastAPI application
    """
    # Create configuration object
    config = AppConfig(
        service_name=service_name,
        service_version=service_version,
        description=description,
        enable_database=enable_database,
        document_models=document_models,
        database_name=database_name,
        enable_auth=enable_auth,
        enable_oauth=enable_oauth,
        public_paths=public_paths,
        cors_origins=cors_origins,
        enable_metrics=enable_metrics,
        enable_health_check=enable_health_check,
        lifespan=lifespan,
    )

    # Application metadata
    app_title = (
        f"{settings.PROJECT_NAME} - "
        f"{(config.service_name).replace('_', ' ').title()} "
        f"[{(settings.ENVIRONMENT).capitalize()}]"
    )
    app_description = config.description or f"{config.service_name} for Quant Platform"

    # Check if we're in development
    is_development = settings.ENVIRONMENT in ["development", "local"]

    # Create lifespan
    lifespan_func = create_lifespan(config)

    # Create FastAPI app
    app = FastAPI(
        title=app_title,
        description=app_description,
        version=config.service_version,
        generate_unique_id_function=custom_generate_unique_id,
        lifespan=lifespan_func,
        docs_url="/docs" if is_development else None,
        redoc_url="/redoc" if is_development else None,
        openapi_url="/openapi.json" if is_development else None,
    )

    # Add CORS middleware
    final_cors_origins = config.cors_origins or settings.all_cors_origins
    if final_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=final_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add authentication middleware (if enabled and not in development)
    if config.enable_auth and not is_development:
        # TODO: Implement authentication middleware
        logger.info("🔐 Authentication middleware would be added here")

    # Add metrics middleware
    if config.enable_metrics:
        try:
            from ..metrics import MetricsMiddleware, get_metrics_collector

            # Initialize metrics collector first
            create_metrics_middleware(config.service_name)
            # Add middleware with collector
            collector = get_metrics_collector()
            app.add_middleware(MetricsMiddleware, collector=collector)
            logger.info(f"📊 Metrics middleware enabled for {config.service_name}")
        except Exception as e:
            logger.error(f"⚠️ Failed to add metrics middleware: {e}")

    # Add health check endpoints
    if config.enable_health_check:
        health_router = create_health_router(
            config.service_name, config.service_version
        )
        app.include_router(health_router)
        logger.info(f"❤️ Health check endpoints added for {config.service_name}")

    # Include auth routers if enabled
    if config.enable_auth:
        from ..auth.router import auth_router, user_router

        app.include_router(
            auth_router, prefix=f"/api/{settings.AUTH_API_VERSION}/auth", tags=["Auth"]
        )
        app.include_router(
            user_router, prefix=f"/api/{settings.AUTH_API_VERSION}/users", tags=["User"]
        )
        # Register auth exception handlers
        register_auth_exception_handlers(app)
        logger.info(
            f"🔐 Auth routes and exception handlers added for {config.service_name}"
        )
        # Include OAuth2 routers if enabled
        if config.enable_oauth:
            try:
                from ..auth.router import oauth2_router

                app.include_router(
                    oauth2_router,
                    prefix=f"/api/{settings.AUTH_API_VERSION}",
                )
                logger.info(f"🔐 OAuth2 routes added for {config.service_name}")
            except Exception as e:
                logger.error(f"⚠️ Failed to include OAuth2 router: {e}")

    return app
