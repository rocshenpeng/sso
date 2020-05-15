# coding: utf8
from django.conf import settings
from django.db.models import Q
from rest_framework import exceptions
from rest_framework.permissions import BasePermission

from core.libs.utils import is_super_user, get_resource_by_user_and_app
from core.models import Group, Role, Resource, User, App

request_method_action_maps = {
    'options': 'read',
    'get': 'read',
    'post': 'add',
    'put': 'update',
    'patch': 'update',
    'delete': 'delete'
}


def check_user_has_permission(user, app_name, resource_name):
    if not isinstance(user, User):
        return False
    # 检测是否为超级管理员
    if is_super_user(user):
        return True
    try:
        app = App.objects.get(name=app_name)
    except App.DoesNotExist:
        raise exceptions.PermissionDenied("invalid app name {}".format(app_name))
    resource = Resource.objects.filter(Q(name=resource_name) & Q(app=app))
    if resource.exists():
        return resource.first() in get_resource_by_user_and_app(user, app)
    else:
        raise exceptions.PermissionDenied("invalid resource {} or app {}".format(resource_name, app_name))


class CheckUserPermission(BasePermission):
    def has_permission(self, request, view):
        # 检测用户是否登录
        user = getattr(request, 'user', None)
        if not (user and user.is_authenticated):
            raise exceptions.NotAuthenticated
        # 检测是否为超级管理员
        if is_super_user(user):
            return True
        app_name = getattr(view, 'app_name', None)
        resource_name = getattr(view, 'resource_name', None)
        if not app_name:
            raise NotImplementedError("property app_name was not set in the view {}".format(view.__class__.__name__))
        if not resource_name:
            raise NotImplementedError(
                "property resource_name was not set in the view {}".format(view.__class__.__name__))
        action_map = request_method_action_maps.get(request.method.lower())
        return check_user_has_permission(user, app_name, "{}{}".format(action_map, resource_name))


# 始终有权限
class AllowPermission(BasePermission):
    def has_permission(self, request, view):
        return True


# 始终无权限
class DenyPermission(BasePermission):
    def has_permission(self, request, view):
        return False
