# coding: utf8
from django.conf.urls import url
from django.urls import include
from rest_framework import routers
from core.views import auth
from core.views.basic import MenuViewSet, RoleViewSet, AppViewSet, ResourceViewSet, UserViewSet, GroupViewSet

router = routers.DefaultRouter()
router.register('app', AppViewSet)
router.register('role', RoleViewSet)
router.register('menu', MenuViewSet)
router.register('resource', ResourceViewSet)
router.register('user', UserViewSet)
router.register('group', GroupViewSet)

urlpatterns = [
    url(r'login$', auth.login),
    url(r'logout$', auth.logout),
    url(r'get_token_by_ticket$', auth.get_token_by_ticket),
    url(r'', include(router.urls)),
]
