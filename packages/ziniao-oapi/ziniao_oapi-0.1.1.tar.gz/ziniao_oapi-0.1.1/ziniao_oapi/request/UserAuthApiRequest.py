#!/usr/bin/python
# -*- coding: UTF-8 -*-
from ziniao_oapi.common import RequestTypes
from ziniao_oapi.request.BaseRequest import BaseRequest


class UserAuthApiRequest(BaseRequest):
    """获取用户已授权接口"""

    def __init__(self):
        BaseRequest.__init__(self)

    def get_method(self):
        return '/user/get_auth_api'

    def get_request_type(self):
        return RequestTypes.POST_JSON
