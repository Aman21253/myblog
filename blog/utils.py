from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def login_required_y(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("user_id"):
            messages.error(request, "Please login first.")
            return redirect("y_login")
        return view_func(request, *args, **kwargs)
    return _wrapped

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            role = request.session.get("user_role")
            if role not in allowed_roles:
                messages.error(request, "Access denied.")
                return redirect("y_home")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator