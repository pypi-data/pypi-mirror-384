#!/usr/bin/python
# -*- coding: UTF-8 -*-
from ziniao_oapi.common import RequestTypes
from ziniao_oapi.request.BaseRequest import BaseRequest


class UserTokenRequest(BaseRequest):
    """获取会员信息请求"""

    def __init__(self):
        BaseRequest.__init__(self)

    def get_method(self):
        return '/auth/get_user_token'

    def get_version(self):
        return '1.0'

    def get_request_type(self):
        return RequestTypes.POST_JSON
