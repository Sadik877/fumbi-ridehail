from functools import wraps

from flask import abort
from flask_login import current_user


def roles_required(*roles):
    """Restrict a view to one or more UserRole values.

    Usage:
        @roles_required(UserRole.DRIVER)
        def driver_dashboard(): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            role_values = {r.value if hasattr(r, "value") else r for r in roles}
            if current_user.role.value not in role_values:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
