import hmac
import secrets
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import get_settings


router = APIRouter(prefix="/admin", tags=["Admin"])

SESSION_ADMIN_KEY = "admin_authenticated"
SESSION_ADMIN_USERNAME_KEY = "admin_username"
SESSION_CSRF_KEY = "admin_csrf_token"


def get_templates(request: Request) -> Any:
    """Return configured Jinja templates from application state."""

    return request.app.state.templates


def create_csrf_token(request: Request) -> str:
    """Create and save a CSRF token in the current session."""

    token = secrets.token_urlsafe(32)
    request.session[SESSION_CSRF_KEY] = token
    return token


def is_admin_authenticated(request: Request) -> bool:
    """Check whether current browser session belongs to an admin."""

    return request.session.get(SESSION_ADMIN_KEY) is True


def redirect_to_login() -> RedirectResponse:
    """Redirect unauthenticated users to login page."""

    return RedirectResponse(url="/admin/login", status_code=303)


def render_login(
    request: Request,
    error: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    """Render login page."""

    csrf_token = create_csrf_token(request)

    return get_templates(request).TemplateResponse(
        request=request,
        name="admin/login.html",
        context={
            "app_name": get_settings().app_name,
            "error": error,
            "csrf_token": csrf_token,
        },
        status_code=status_code,
    )


@router.get("", response_class=HTMLResponse, include_in_schema=False)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def admin_dashboard(request: Request) -> HTMLResponse | RedirectResponse:
    """Render the protected admin dashboard."""

    if not is_admin_authenticated(request):
        return redirect_to_login()

    settings = get_settings()

    return get_templates(request).TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "admin_username": request.session.get(
                SESSION_ADMIN_USERNAME_KEY,
                settings.admin_username,
            ),
        },
    )


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def admin_login_page(
    request: Request,
) -> HTMLResponse | RedirectResponse:
    """Render admin login page."""

    if is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    return render_login(request)


@router.post("/login", response_class=HTMLResponse, include_in_schema=False)
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
) -> HTMLResponse | RedirectResponse:
    """Authenticate an administrator and create an authenticated session."""

    settings = get_settings()

    session_csrf_token = request.session.get(SESSION_CSRF_KEY, "")

    csrf_is_valid = hmac.compare_digest(
        csrf_token,
        session_csrf_token,
    )

    username_is_valid = hmac.compare_digest(
        username.strip(),
        settings.admin_username,
    )

    password_is_valid = hmac.compare_digest(
        password,
        settings.admin_password,
    )

    if not (csrf_is_valid and username_is_valid and password_is_valid):
        return render_login(
            request=request,
            error="نام کاربری، رمز عبور یا درخواست امنیتی معتبر نیست.",
            status_code=401,
        )

    request.session.clear()
    request.session[SESSION_ADMIN_KEY] = True
    request.session[SESSION_ADMIN_USERNAME_KEY] = settings.admin_username

    return RedirectResponse(url="/admin", status_code=303)


@router.post("/logout", include_in_schema=False)
async def admin_logout(
    request: Request,
    csrf_token: str = Form(...),
) -> RedirectResponse:
    """Destroy authenticated admin session."""

    session_csrf_token = request.session.get(SESSION_CSRF_KEY, "")

    if csrf_token and hmac.compare_digest(csrf_token, session_csrf_token):
        request.session.clear()

    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("/logout", include_in_schema=False)
async def admin_logout_get() -> RedirectResponse:
    """
    Redirect GET logout requests to login.

    Actual logout requires POST and CSRF validation.
    """

    return RedirectResponse(url="/admin/login", status_code=303)