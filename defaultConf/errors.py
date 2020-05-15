# coding: utf8
from core.libs.response import ServerErrorResponse, PageNotFoundResponse


def page_not_found(request, *args, **kwargs):
    return PageNotFoundResponse(msg="Invalid request path: {}".format(request.path))


def page_server_error(request, *args, **kwargs):
    return ServerErrorResponse()
