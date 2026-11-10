from fastapi import APIRouter, Cookie, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.deps import current_user
from app.auth.models import User
from app.core.db import get_session
from app.core.errors import UnauthorizedError
from app.core.security import AttemptLimiter
from app.core.settings import get_settings

login_limiter = AttemptLimiter(limit=20, window_s=600)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


class RoleOut(BaseModel):
    code: str
    counter_id: int | None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    roles: list[RoleOut]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[RoleOut(code=r.role.code, counter_id=r.counter_id) for r in user.roles],
    )


def _set_cookie(response: Response, raw: str) -> None:
    s = get_settings()
    response.set_cookie(
        s.refresh_cookie_name,
        raw,
        max_age=s.refresh_token_ttl_days * 86400,
        httponly=True,
        secure=s.app_env != "dev",
        samesite="strict",
        path="/auth",
    )


@router.post("/login", response_model=TokenOut)
def login(
    body: LoginIn, request: Request, response: Response, db: Session = Depends(get_session)
) -> TokenOut:
    ip = request.client.host if request.client else "?"
    keys = (f"ip:{ip}", f"em:{body.email.strip().lower()}")
    for k in keys:  # brute-force / credential-stuffing guard: only FAILED logins count
        login_limiter.check(k)
    try:
        user, access, refresh = service.login(db, body.email, body.password)
    except UnauthorizedError:
        for k in keys:
            login_limiter.fail(k)
        raise
    login_limiter.clear(keys[1])
    _set_cookie(response, refresh)
    return TokenOut(access_token=access, user=user_out(user))


@router.post("/refresh", response_model=TokenOut)
def refresh(
    response: Response,
    db: Session = Depends(get_session),
    token: str | None = Cookie(default=None, alias=get_settings().refresh_cookie_name),
) -> TokenOut:
    if not token:
        raise UnauthorizedError("Missing refresh token")
    user, access, new_refresh = service.refresh(db, token)
    _set_cookie(response, new_refresh)
    return TokenOut(access_token=access, user=user_out(user))


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    db: Session = Depends(get_session),
    token: str | None = Cookie(default=None, alias=get_settings().refresh_cookie_name),
) -> None:
    service.logout(db, token)
    response.delete_cookie(get_settings().refresh_cookie_name, path="/auth")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> UserOut:
    return user_out(user)
