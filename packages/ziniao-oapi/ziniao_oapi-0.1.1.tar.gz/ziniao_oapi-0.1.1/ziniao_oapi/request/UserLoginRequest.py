#!/usr/bin/python
# -*- coding: UTF-8 -*-
from ziniao_oapi.common import RequestTypes
from ziniao_oapi.request.BaseRequest import BaseRequest

class UserLoginRequest(BaseRequest):
    def __init__(self):
        BaseRequest.__init__(self)

    def get_method(self):
        return "/superbrowser/rest/v1/token/user-login"

    def get_request_type(self):
        return RequestTypes.POST_JSON
