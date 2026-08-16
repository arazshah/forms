from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.templating import Jinja2Templates

from app.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.app_debug,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="araz_forms_session",
    max_age=60 * 60 * 12,
    same_site="lax",
    https_only=settings.app_secure_cookies,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request) -> HTMLResponse:
    """Render the public landing page."""

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
        },
    )


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health endpoint used by Docker and Coolify."""

    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
    }