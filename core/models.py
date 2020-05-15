# coding: utf8
import uuid

from django.contrib.auth.hashers import make_password, check_password
from django.db import models

from core.libs.validators import UsernameValidator, NameValidator, ServerPortValidator, NoneSpecialValidator, \
    NonSpaceValidator

username_validator = UsernameValidator()
name_validator = NameValidator()
server_port_validator = ServerPortValidator()
none_special_validator = NoneSpecialValidator()
non_space_validator = NonSpaceValidator()


# 为新增条目设置默认sort_id为其主键id
def set_default_sort_id(obj):
    print(obj, obj.id)
    if not obj.sort_id:
        obj.sort_id = obj.id
        obj.save(update_fields=["sort_id"])
    return obj


class BaseModel(models.Model):
    class Meta:
        abstract = True

    required_fields = ["name", "description"]


# 应用表
class App(BaseModel):
    name = models.CharField(max_length=50, unique=True, validators=[name_validator], verbose_name="应用名称")
    description = models.CharField(max_length=100, verbose_name="应用描述")

    def __str__(self):
        return self.name


# 用户表
class User(BaseModel):
    username = models.CharField(max_length=100, unique=True, validators=[username_validator], verbose_name="用户登录名")
    _password = models.CharField(db_column="password", max_length=78, null=True, verbose_name="密码")
    cname = models.CharField(max_length=100, validators=[non_space_validator], verbose_name="用户显示名")
    email = models.EmailField(unique=True, max_length=100, verbose_name="邮箱")
    is_active = models.BooleanField(default=True, verbose_name="用户是否可用")
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="最后登录时间")

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['cname', 'email']
    required_fields = ["username", "cname", "email"]

    @property
    def name(self):
        return self.username

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    @property
    def password(self):
        return None

    @password.setter
    def password(self, secret):
        self._password = make_password(str(secret))

    def check_password(self, secret):
        return check_password(secret, self._password)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        token = Token.objects.filter(user__username=self.username)
        if not token.exists():
            token = Token()
            token.key = uuid.uuid4().hex
            token.user = self
            token.save()


# 用户token表
class Token(models.Model):
    key = models.CharField(unique=True, max_length=32, validators=[non_space_validator], verbose_name="用户token")
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="关联的用户")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = uuid.uuid4().hex
        super().save(*args, **kwargs)
        return self

    def __str__(self):
        return self.user.username

    def reset_token(self):
        self.key = uuid.uuid4().hex
        return self.save(update_fields=["key"])


# 用户组表
class Group(BaseModel):
    name = models.CharField(max_length=100, unique=True, validators=[name_validator], verbose_name="用户组名称")
    description = models.CharField(max_length=100, verbose_name="组描述")
    user = models.ManyToManyField(User, verbose_name="该组所包含的用户")

    def __str__(self):
        return self.name


# 角色表
class Role(BaseModel):
    name = models.CharField(max_length=100, validators=[name_validator], verbose_name="角色名称")
    description = models.CharField(max_length=100, verbose_name="角色描述")
    app = models.ForeignKey(App, on_delete=models.ProtectedError, verbose_name="角色所属应用")
    user = models.ManyToManyField(User, verbose_name="该角色所包含的用户")
    group = models.ManyToManyField(Group, verbose_name="该角色所包含的组")

    class Meta:
        # 角色名与应用ID生成复合主键
        unique_together = ("name", "app")

    def __str__(self):
        return "{}/{}".format(self.app.name, self.name)


# 菜单表
class Menu(BaseModel):
    name = models.CharField(max_length=100, validators=[name_validator], verbose_name="菜单名称")
    description = models.CharField(max_length=100, verbose_name="菜单描述")
    url = models.CharField(max_length=100, validators=[non_space_validator], verbose_name="菜单对应的URL路径")
    icon = models.CharField(default="fa-list", max_length=50, validators=[none_special_validator],
                            verbose_name="菜单对应的图标名称")
    parent = models.ForeignKey("Menu", on_delete=models.ProtectedError, null=True, verbose_name="父菜单")
    public = models.BooleanField(default=False, verbose_name="是否为公共访问菜单")
    available = models.BooleanField(default=True, verbose_name="是否可用")
    sort_id = models.IntegerField(default=0, verbose_name="菜单排序标识")
    app = models.ForeignKey(App, on_delete=models.ProtectedError, verbose_name="菜单所属应用")

    class Meta:
        # 菜单名与应用ID生成复合主键
        unique_together = ("name", "app")

    def __str__(self):
        return "{}/{}".format(self.app.name, self.name)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        return set_default_sort_id(self)

    required_fields = ["name", "description", "url"]


# 资源表
class Resource(BaseModel):
    name = models.CharField(max_length=100, validators=[name_validator], verbose_name="资源名称")
    description = models.CharField(max_length=100, verbose_name="资源描述")
    parent = models.ForeignKey("Resource", on_delete=models.ProtectedError, null=True, verbose_name="父资源")
    available = models.BooleanField(default=True, verbose_name="资源是否可用")
    sort_id = models.IntegerField(default=0, verbose_name="资源排序标识")
    app = models.ForeignKey(App, on_delete=models.ProtectedError, verbose_name="资源所属应用")
    menu = models.ForeignKey(Menu, on_delete=models.ProtectedError, verbose_name="资源所属菜单")
    role = models.ManyToManyField(Role, verbose_name="该资源被哪些角色引用")

    class Meta:
        # 资源名与应用ID生成复合主键
        unique_together = ("name", "app")

    def __str__(self):
        return "{}/{}".format(self.app.name, self.name)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        return set_default_sort_id(self)
