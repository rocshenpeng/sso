# coding: utf8

import uuid
from django.contrib import auth
from django.core.cache import cache
from rest_framework.decorators import api_view
from core.libs import utils
from core.libs.response import ApiResponse, UnauthorizedResponse, BadRequestResponse
from core.models import User


def return_user_or_ticket(request, user):
    redirect_url = request.GET.get('redirect')
    if redirect_url:
        ticket = generate_temp_token(user.id, token_type="ticket")
        params_connect_flag = '&' if '?' in redirect_url else '?'
        redirect_url = "{}{}ticket={}".format(redirect_url, params_connect_flag, ticket)
        data = {"type": "redirect", "redirect": redirect_url}
    else:
        auth.login(request, user)
        tmp_token = generate_temp_token(user.id)
        data = {"type": "login", "token": tmp_token}
    return ApiResponse(data=data)


@api_view(["GET", "POST"])
def login(request):
    if request.user.is_authenticated:
        return return_user_or_ticket(request, request.user)
    if request.method == 'GET':
        username = request.GET.get('username')
        password = request.GET.get('password')
    else:
        username = request.data.get('username')
        password = request.data.get('password')
    try:
        if not username:
            return UnauthorizedResponse(msg="username can't be null")
        if not password:
            return UnauthorizedResponse(msg="password can't be null")
        user = auth.authenticate(request, username=username, password=password)
        if user:
            return return_user_or_ticket(request, user)
        else:
            return UnauthorizedResponse(msg="Invalid username or password")
    except Exception as e:
        return UnauthorizedResponse(msg=e.__str__())


@api_view(["GET"])
def logout(request):
    try:
        if request.user.is_authenticated:
            auth.logout(request)
    except Exception as e:
        print(e.__str__())
    return ApiResponse(msg='logout success')


def generate_temp_token(user_id, token_type="token"):
    token_str = uuid.uuid4().hex
    cache_prefix = utils.TMP_TOKEN_PREFIX
    expire = utils.TMP_TOKEN_TIMEOUT
    if token_type == 'ticket':
        cache_prefix = utils.TMP_TICKET_PREFIX
        expire = utils.TMP_TICKET_TIMEOUT
    cache.set("{}:{}".format(cache_prefix, token_str), user_id, expire)
    return token_str


@api_view(["GET"])
def get_token_by_ticket(request):
    ticket = request.GET.get("ticket")
    if not ticket:
        return UnauthorizedResponse("parameter ticket is required.")
    ticket_key = "{}:{}".format(utils.TMP_TICKET_PREFIX, ticket)
    user_id = cache.get(ticket_key)
    cache.delete(ticket_key)
    if not user_id:
        return UnauthorizedResponse("invalid ticket or ticket already expired.")
    tmp_token = generate_temp_token(user_id)
    user = User.objects.get(id=user_id)
    user_info = {
        "username": user.username,
        "cname": user.cname,
        "email": user.email
    }
    return ApiResponse(data={"token": tmp_token, "user": user_info})
