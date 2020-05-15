# coding: utf8

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from core.libs import utils
from core.models import Token

UserModel = get_user_model()


class SessionAuthentication(BaseAuthentication):
    def authenticate(self, request):
        user = getattr(request._request, 'user', None)
        if not (user and user.is_authenticated):
            return None
        elif not user.is_active:
            raise exceptions.AuthenticationFailed("User inactive")
        else:
            return user, None


class TokenAuthentication(BaseAuthentication):
    keyword = utils.ACCESS_TOKEN_HEADER_STRING
    is_active_key = 'is_active'
    model = Token

    def authenticate(self, request):
        access_token = utils.get_token(request, self.keyword)
        if not access_token:
            return None
        return self.authenticate_credentials(access_token)

    def authenticate_credentials(self, key):
        model = self.model
        try:
            token = model.objects.get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token")
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive")
        return token.user, token

    def authenticate_header(self, request):
        return self.keyword


class TmpTokenAuthentication(TokenAuthentication):
    token_prefix = utils.TMP_TOKEN_PREFIX
    keyword = utils.TMP_TOKEN_HEADER_STRING
    timeout = utils.TMP_TOKEN_TIMEOUT

    def authenticate_credentials(self, key):
        token_key = "{}:{}".format(self.token_prefix, key)
        try:
            user_id = cache.get(token_key)
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token.")
        if not user.is_active:
            raise exceptions.AuthenticationFailed("User inactive")
        # 刷新临时token的过期时间
        cache.expire(token_key, self.timeout)
        return user, key
