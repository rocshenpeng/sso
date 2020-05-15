# coding: utf8

import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from rest_framework import exceptions
from core.libs.auth import LDAPAuth
from core.models import User, Token
from core.serializer import UserSerializer

UserModel = get_user_model()



def get_or_create_user(user_info):
    user = User.objects.filter(username=user_info['username'])
    if user.exists():
        return user.first()
    else:
        user = {
            "username": user_info['username'],
            "cname": user_info['displayName'],
            "email": user_info['mail'],
            "token": uuid.uuid4().hex,
        }
        serializer = UserSerializer(data=user)
        if serializer.is_valid():
            user = serializer.save()
            return user
        else:
            raise Exception(serializer.errors)


class LDAPAuthBackend(ModelBackend):
    def __init__(self):
        self.ldap_host = getattr(settings, "LDAP_HOST", "localhost")
        self.ldap_port = getattr(settings, "LDAP_PORT", 389)
        self.ldap_search_base = getattr(settings, "LDAP_SEARCH_BASE", None)
        self.admin_dn = getattr(settings, "LDAP_ADMIN_DN", None)
        self.admin_password = getattr(settings, "LDAP_ADMIN_PASSWORD", None)

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username and password:
            ldap_auth = LDAPAuth(host=self.ldap_host, port=self.ldap_port, search_base=self.ldap_search_base,
                                 admin_dn=self.admin_dn, admin_password=self.admin_password)
            user_info = ldap_auth.auth(username, password)
            if user_info:
                user = get_or_create_user(user_info)
                user.password = password
                user.save()
                if self.user_can_authenticate(user):
                    return user
            else:
                raise exceptions.AuthenticationFailed("Invalid username or password.")
