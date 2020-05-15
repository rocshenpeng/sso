# coding: utf8
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        code = getattr(type(exc), 'status_code', 404)
        res = {
            "code": code,
            "msg": response.data.get('detail', response.data),
            'data': '',
        }
        response.data = res
        response.status_code = 200

    return response
