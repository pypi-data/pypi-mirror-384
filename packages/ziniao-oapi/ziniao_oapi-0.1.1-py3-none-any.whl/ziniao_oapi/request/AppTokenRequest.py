#!/usr/bin/python
# -*- coding: UTF-8 -*-
from ziniao_oapi.common import RequestTypes
from ziniao_oapi.request.BaseRequest import BaseRequest


class AppTokenRequest(BaseRequest):
    """获取应用token请求"""

    def __init__(self):
        BaseRequest.__init__(self)

    def get_method(self):
        return '/auth/get_app_token'

    def get_request_type(self):
        return RequestTypes.POST_JSON
