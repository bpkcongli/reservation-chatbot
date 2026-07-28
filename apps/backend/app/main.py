from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.catalog.api import router as catalog_router
from app.modules.conversation.api import router as conversation_router
from app.shared.config import get_settings
from app.shared.errors import register_error_handlers
from app.shared.health import router as health_router
from app.shared.observability import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_debug,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(settings.frontend_origin).rstrip("/")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(application)
    application.include_router(health_router, prefix=settings.api_v1_prefix)
    application.include_router(catalog_router, prefix=settings.api_v1_prefix)
    application.include_router(conversation_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
