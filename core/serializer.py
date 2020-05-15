# coding: utf8
from rest_framework.serializers import ModelSerializer

from core.models import App, User, Group, Role, Menu, Resource


class AppSerializer(ModelSerializer):
    class Meta:
        model = App
        fields = ['id', 'name', 'description']


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'cname', 'email', 'is_active', 'last_login']


class GroupSerializer(ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'description']


class RoleSerializer(ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'app']


class MenuSerializer(ModelSerializer):
    class Meta:
        model = Menu
        fields = ['id', 'name', 'description', 'url', 'icon', 'parent', 'public', 'sort_id', 'available', 'app']


class ResourceSerializer(ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'name', 'description', 'sort_id', 'available', 'parent', 'app', 'menu']
