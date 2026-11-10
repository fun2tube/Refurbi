from collections.abc import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.security import decode_access_token
from app.core.db import get_session
from app.core.errors import ForbiddenError, UnauthorizedError

_bearer = HTTPBearer(auto_error=False)


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_session),
) -> User:
    if creds is None:
        raise UnauthorizedError("Not authenticated")
    user = db.get(User, decode_access_token(creds.credentials))
    if user is None or not user.is_active:
        raise UnauthorizedError("Not authenticated")
    return user


def user_permissions(user: User, counter_id: int | None = None) -> set[str]:
    """Permissions the user holds, optionally for one counter.

    A global role assignment (counter_id NULL) applies everywhere. A counter-scoped assignment
    applies only to that counter, and never to counter-less (global) actions.
    """
    perms: set[str] = set()
    for ur in user.roles:
        if ur.counter_id is None or (counter_id is not None and ur.counter_id == counter_id):
            perms.update(p.code for p in ur.role.permissions)
    return perms


def has_permission(user: User, permission: str, counter_id: int | None = None) -> bool:
    return permission in user_permissions(user, counter_id)


def require_permission(permission: str, counter_param: str | None = None) -> Callable[..., User]:
    """Dependency factory. If counter_param is given, the named path/query parameter is read as
    the counter id and the permission must be held globally or for that counter."""

    def dependency(request: Request, user: User = Depends(current_user)) -> User:
        counter_id: int | None = None
        if counter_param:
            raw = request.path_params.get(counter_param) or request.query_params.get(counter_param)
            try:
                counter_id = int(raw) if raw is not None else None
            except ValueError:
                raise ForbiddenError("Forbidden") from None
        if not has_permission(user, permission, counter_id):
            raise ForbiddenError("You do not have permission to do this")
        return user

    return dependency
