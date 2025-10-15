#!/usr/bin/python
# -*- coding: UTF-8 -*-
from ziniao_oapi.common import RequestTypes
from ziniao_oapi.request.BaseRequest import BaseRequest


class UserOpenIdRequest(BaseRequest):
    """获取用户的openId"""

    def __init__(self):
        BaseRequest.__init__(self)

    def get_method(self):
        return '/user/get_open_id'

    def get_request_type(self):
        return RequestTypes.POST_JSON
