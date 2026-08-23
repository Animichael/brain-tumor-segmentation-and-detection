from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(view):
    """Restrict a view to authenticated users with the admin role."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped
