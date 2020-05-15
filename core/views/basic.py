# coding: utf8
from rest_framework import exceptions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from core.libs.authentication import TokenAuthentication, TmpTokenAuthentication, SessionAuthentication
from core.libs.permissions import CheckUserPermission, check_user_has_permission
from core.libs.response import BadRequestResponse, ApiResponse, ForbiddenResponse
from core.libs import utils
from core.libs.exception import api_exception_handler
from core.models import Menu, App, Role, Resource, Group, User
from core.serializer import MenuSerializer, AppSerializer, RoleSerializer, ResourceSerializer, GroupSerializer, \
    UserSerializer


def format_response(response):
    data = {
        "code": response.status_code,
        "msg": "ok",
        "data": response.data,
    }
    response.data = data
    return response


def check_pk_is_exist(model, pk_list):
    model_name = model.__name__.lower()
    if isinstance(pk_list, list):
        for pk in pk_list:
            try:
                model.objects.get(id=pk)
            except model.DoesNotExist:
                raise exceptions.ParseError("{} id {} does not exist".format(model_name, pk))
            except Exception as e:
                raise exceptions.ParseError("invalid {} id {}".format(model_name, pk))
    else:
        raise exceptions.ParseError("parameter {} is null or not a list".format(model_name))


def extend_many_to_many_url(request, obj, related_obj, serializer_class):
    related_mode = serializer_class.Meta.model
    serializer = serializer_class(related_obj.all(), many=True)
    if request.method == "GET":
        return ApiResponse(data=serializer.data)
    elif request.method in ["POST", "PUT"]:
        pk_list = request.data.get("id")
        check_pk_is_exist(related_mode, pk_list)
        related_obj.set(pk_list)
    else:
        related_obj.clear()
    obj.save()
    return ApiResponse(msg="process success", data=serializer.data)


def get_end_url_path(url_path):
    path_list = url_path.split('/')
    return path_list[-2] if url_path.endswith('/') else path_list[-1]


class AuthenticationView(APIView):
    renderer_classes = [JSONRenderer]
    authentication_classes = [SessionAuthentication, TokenAuthentication, TmpTokenAuthentication]
    permission_classes = (IsAuthenticated,)

    def get_exception_handler(self):
        return api_exception_handler


class PermissionView(AuthenticationView):
    permission_classes = (CheckUserPermission,)
    app_name = utils.APP_NAME

    @property
    def resource_name(self):
        return self.__class__.__name__.replace('ViewSet', '')


class BaseView(PermissionView, ModelViewSet):
    uk_name_list = ['name']
    model = None
    error_msg = None
    authenticate_permission_path = None

    def get_old_obj(self, uk_name, uk_value):
        kwargs = {uk_name: uk_value}
        return self.model.objects.get(**kwargs)

    def check_uk_is_exist(self, request, action_type):
        self.model = self.get_serializer().Meta.model
        for uk_name in self.uk_name_list:
            try:
                uk_value = request.data.get(uk_name)
                self.error_msg = "{}: {} already exist.".format(uk_name, uk_value)
                old_obj = self.get_old_obj(uk_name, uk_value)
                if action_type == "create":
                    raise exceptions.ParseError(detail=self.error_msg)
                else:
                    if old_obj != self.get_object():
                        raise exceptions.ParseError(detail=self.error_msg)
            except self.model.DoesNotExist:
                pass
        return False

    def list(self, request, *args, **kwargs):
        return format_response(super().list(request, *args, **kwargs))

    def retrieve(self, request, *args, **kwargs):
        return format_response(super().retrieve(request, *args, **kwargs))

    def create(self, request, *args, **kwargs):
        self.check_uk_is_exist(request, "create")
        return format_response(super().create(request, *args, **kwargs))

    def update(self, request, *args, **kwargs):
        self.check_uk_is_exist(request, "update")
        return format_response(super().update(request, *args, **kwargs))

    def destroy(self, request, *args, **kwargs):
        return format_response(super().destroy(request, *args, **kwargs))

    # 重新设置权限级别，指定的URL允许通过认证的用户即可访问
    def get_permissions(self):
        if self.authenticate_permission_path and (
                get_end_url_path(self.request.path) in self.authenticate_permission_path):
            return [IsAuthenticated()]
        return super().get_permissions()


class ExtendUserView:
    def get_user_related_obj(self):
        raise NotImplementedError("you must override this function")

    @action(detail=True, methods=["GET", "POST", "PUT", "DELETE"])
    def user(self, request, pk=None):
        return extend_many_to_many_url(request, self.get_object(), self.get_user_related_obj(), UserSerializer)


class ExtendGroupView:
    def get_group_related_obj(self):
        raise NotImplementedError("you must override this function")

    @action(detail=True, methods=["GET", "POST", "PUT", "DELETE"])
    def group(self, request, pk=None):
        return extend_many_to_many_url(request, self.get_object(), self.get_group_related_obj(), GroupSerializer)


class ExtendRoleView:
    def get_role_related_obj(self):
        raise NotImplementedError("you must override this function")

    @action(detail=True, methods=["GET", "POST", "PUT", "DELETE"])
    def role(self, request, pk=None):
        return extend_many_to_many_url(request, self.get_object(), self.get_role_related_obj(), RoleSerializer)


class ExtendSortedFormatView:
    @action(detail=False, methods=["GET"])
    def format(self, request):
        obj_list = utils.sort_obj(self.queryset, self.serializer_class)
        return ApiResponse(data=obj_list)


class ExtendGetObjectByAppView:
    def get_object_list(self, app):
        return self.serializer_class(self.queryset.filter(app=app), many=True).data

    @action(detail=False, methods=["GET"])
    def get_obj_by_app(self, request):
        app = utils.get_obj_by_request_param(request, App, param_id="id")
        return ApiResponse(data=self.get_object_list(app))


class AppViewSet(BaseView):
    queryset = App.objects.all()
    serializer_class = AppSerializer

    def destroy(self, request, *args, **kwargs):
        app = self.get_object()
        if app.menu_set.all().exists():
            model_name = "菜单"
        elif app.role_set.all().exists():
            model_name = "角色"
        elif app.resource_set.all().exists():
            model_name = "资源"
        else:
            return super().destroy(request, *args, **kwargs)
        return BadRequestResponse(msg="删除失败，存在与之关联的{}".format(model_name))


class RoleViewSet(BaseView, ExtendUserView, ExtendGroupView, ExtendGetObjectByAppView):
    model = None
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_user_related_obj(self):
        return self.get_object().user

    def get_group_related_obj(self):
        return self.get_object().group

    @action(detail=True, methods=["GET", "POST", "PUT", "DELETE"])
    def resource(self, request, pk=None):
        role = self.get_object()
        if request.method == "GET":
            return ApiResponse(data=ResourceSerializer(utils.get_resource_by_role(role), many=True).data)
        return extend_many_to_many_url(request, role, role.resource_set, ResourceSerializer)


class MenuViewSet(BaseView, ExtendSortedFormatView, ExtendGetObjectByAppView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    authenticate_permission_path = ['my_menu']

    def destroy(self, request, *args, **kwargs):
        menu = self.get_object()
        if Menu.objects.filter(parent=menu).exists():
            model_name = "子菜单"
        elif menu.resource_set.all().exists():
            model_name = "资源"
        else:
            return super().destroy(request, *args, **kwargs)
        return BadRequestResponse(msg="删除失败，存在与之关联的{}".format(model_name))

    @action(detail=False, methods=["GET"])
    def my_menu(self, request):
        app = utils.get_obj_by_request_param(request, App, param_name="app_name")
        menus = utils.get_menu_by_user_and_app(request.user, app)
        return ApiResponse(data=menus)

    def get_object_list(self, app):
        return utils.sort_obj(self.queryset.filter(app=app), self.serializer_class)


class ResourceViewSet(BaseView, ExtendSortedFormatView, ExtendGetObjectByAppView):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer

    def destroy(self, request, *args, **kwargs):
        resource = self.get_object()
        if Resource.objects.filter(parent=resource).exists():
            model_name = "子资源"
        else:
            return super().destroy(request, *args, **kwargs)
        return BadRequestResponse(msg="删除失败，存在与之关联的{}".format(model_name))

    def get_object_list(self, app):
        return utils.sort_obj(self.queryset.filter(app=app), self.serializer_class)


class GroupViewSet(BaseView, ExtendUserView, ExtendRoleView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_user_related_obj(self):
        return self.get_object().user

    def get_role_related_obj(self):
        return self.get_object().role_set


class UserViewSet(BaseView, ExtendGroupView, ExtendRoleView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    uk_name_list = ['username', 'email']
    authenticate_permission_path = ['token', 'myself', 'has_permission', 'permission']

    @action(detail=False, methods=["GET", "POST", "PUT"])
    def token(self, request):
        if request.method in ["POST", "PUT"]:
            request.user.token.reset_token()
        return ApiResponse(data=request.user.token.key)

    # 重置用户密码
    @action(detail=False, methods=["POST"])
    def password(self, request):
        pass

    @action(detail=False, methods=["GET"])
    def myself(self, request):
        return ApiResponse(data=UserSerializer(request.user).data)

    @action(detail=False, methods=["GET"])
    def has_permission(self, request):
        app_name = utils.get_param_or_exception(request, "app_name")
        permission_name = utils.get_param_or_exception(request, "permission_name")
        if check_user_has_permission(request.user, app_name, permission_name):
            return ApiResponse()
        return ForbiddenResponse()

    @action(detail=False, methods=["GET"])
    def permission(self, request):
        app = utils.get_obj_by_request_param(request, App, param_name="app_name")
        resource_name_list = []
        for resource in utils.get_resource_by_user_and_app(request.user, app):
            resource_name_list.append(resource.name)
        return ApiResponse(data=resource_name_list)

    def get_group_related_obj(self):
        return self.get_object().group_set

    def get_role_related_obj(self):
        return self.get_object().role_set
