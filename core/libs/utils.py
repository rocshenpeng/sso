# coding: utf8
from django.conf import settings
from django.db.models import Q
from rest_framework import exceptions

from core.models import Resource, Menu, Role
from core.serializer import MenuSerializer

ACCESS_TOKEN_HEADER_STRING = getattr(settings, "ACCESS_TOKEN_HEADER", "access-token")
TMP_TOKEN_PREFIX = getattr(settings, "TMP_TOKEN_PREFIX", 'token')
TMP_TICKET_PREFIX = getattr(settings, "TMP_TICKET_PREFIX", 'ticket')
TMP_TOKEN_HEADER_STRING = getattr(settings, "TMP_TOKEN_HEADER", "tmp-token")
TMP_TOKEN_TIMEOUT = getattr(settings, "USER_TEMP_TOKEN_TIMEOUT", 1800)
TMP_TICKET_TIMEOUT = getattr(settings, "USER_TEMP_TICKET_TIMEOUT", 300)
SUPER_USERNAME_LIST = getattr(settings, "SUPER_USERNAME_LIST")
APP_NAME = getattr(settings, "DEFAULT_APP_NAME", "sso")


def get_token(request, token_head):
    token_header_name = 'HTTP_{}'.format(token_head.replace('-', '_').upper())
    return request.META.get(token_header_name)


def is_super_user(user):
    if not getattr(user, 'is_authenticated', None):
        return False
    if SUPER_USERNAME_LIST and (user.username in SUPER_USERNAME_LIST):
        return True


def extend_query_set(*args):
    objs = []
    for i in args:
        for j in i:
            if j not in objs:
                objs.append(j)
    return objs


def get_role_by_user_and_app(user, app):
    user_groups = user.group_set.all()
    role_list = Role.objects.filter(app=app).filter(Q(group__in=user_groups) | Q(user=user))
    return role_list


def get_resource_by_user_and_app(user, app):
    if is_super_user(user):
        return Resource.objects.filter(app=app)
    role_list = get_role_by_user_and_app(user, app)
    resource_base_query = Resource.objects.filter(app=app).filter(available=1)
    resource_list = resource_base_query.filter(role__in=role_list)
    children_resource_list = resource_base_query.filter(parent__in=resource_list)
    return extend_query_set(resource_list, children_resource_list)


def get_menu_by_user_and_app(user, app):
    if is_super_user(user):
        menus = Menu.objects.filter(app=app).filter(available=1).order_by("sort_id")
    else:
        menu_base_query = Menu.objects.filter(app=app).filter(available=1)
        resource_list = get_resource_by_user_and_app(user, app)
        menu_list = menu_base_query.filter(resource__in=resource_list).order_by("sort_id")
        children_menu_list = menu_base_query.filter(parent__in=menu_list).order_by("sort_id")
        menus = extend_query_set(menu_list, children_menu_list)
    return sort_obj(menus, MenuSerializer)


def get_resource_by_role(role):
    resource_base_query = Resource.objects.filter(available=1)
    resource_list = resource_base_query.filter(role=role)
    children_resource_list = resource_base_query.filter(parent__in=resource_list)
    return extend_query_set(resource_list, children_resource_list)


def sort_obj(obj_list, serializer, parent=None):
    objs = []
    for obj in obj_list:
        if obj.parent == parent:
            tmp_obj = serializer(obj).data
            tmp_obj["children"] = sort_obj(obj_list, serializer, obj)
            objs.append(tmp_obj)
    return objs


def get_param_or_exception(request, key):
    if request.method == "GET":
        params_dict = request.GET
    else:
        params_dict = request.data
    value = params_dict.get(key)
    if not value:
        raise exceptions.ParseError("parameter {} is required".format(key))
    return value


def get_obj_or_exception(model, pk_id=None, uk_name=None):
    msg_suffix = "id or name"
    try:
        if pk_id:
            msg_suffix = "id {}".format(pk_id)
            return model.objects.get(id=pk_id)
        elif uk_name:
            msg_suffix = "name {}".format(uk_name)
            return model.objects.get(name=uk_name)
    except model.DoesNotExist:
        raise exceptions.ParseError("invalid {} {}".format(model.__name__.lower(), msg_suffix))


def get_obj_by_request_param(request, model, param_id=None, param_name=None):
    pk_id = uk_name = None
    if param_id:
        pk_id = get_param_or_exception(request, param_name)
    elif param_name:
        uk_name = get_param_or_exception(request, param_name)
    return get_obj_or_exception(model, pk_id=pk_id, uk_name=uk_name)
