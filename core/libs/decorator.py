# coding: utf8
import functools
import json

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated

from core.libs.permissions import check_user_has_permission, is_super_user
from core.libs.response import ForbiddenResponse, UnauthorizedResponse, ApiResponse
from core.libs.utils import APP_NAME


def login_required(func):
    @functools.wraps(func)
    def wrapper(request=None, *args, **kwargs):
        user = getattr(request, 'user', None)
        if isinstance(user, AnonymousUser):
            return UnauthorizedResponse()
        return func(request=request, *args, **kwargs)

    return wrapper


def permission_required(permission_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request=None, *args, **kwargs):
            user = getattr(request, 'user', None)
            if not (user and isinstance(user, AnonymousUser)):
                return UnauthorizedResponse()
            if not (user and (is_super_user(user) or check_user_has_permission(user, APP_NAME, permission_name))):
                return ForbiddenResponse()
            return func(request=request, *args, **kwargs)

        return wrapper

    return decorator


def cache_response(timeout=60):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(view_cls, request, *args, **kwargs):
            cache_key_prefix = request.path.replace('/', '_')
            user = getattr(request, 'user', None)
            if user:
                cache_key = "{}_{}".format(cache_key_prefix, user.username)
                cache_value = cache.get(cache_key)
                response = func(view_cls, request, *args, **kwargs)
                if not cache_value:
                    data = {
                        "status_code": response.status_code,
                        "data": response.data,
                    }
                    cache.set(cache_key, json.dumps(data), timeout)
                else:
                    data = json.loads(cache_value)
                    response = ApiResponse(data=data["data"])
                    response.status_code = data["status_code"]
                return response
            return func(view_cls, request, *args, **kwargs)

        return wrapper

    return decorator
