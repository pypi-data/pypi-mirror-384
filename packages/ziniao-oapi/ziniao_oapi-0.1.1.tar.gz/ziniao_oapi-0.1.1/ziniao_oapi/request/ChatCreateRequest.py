#!/usr/bin/python
# -*- coding: UTF-8 -*-
from ziniao_oapi.common import RequestTypes
from ziniao_oapi.request.BaseRequest import BaseRequest


class ChatCreateRequest(BaseRequest):
    """AI非流会话"""

    def __init__(self):
        BaseRequest.__init__(self)

    def get_method(self):
        return '/linkfox-ai/chat/v1/completion/create'

    def get_request_type(self):
        return RequestTypes.POST_JSON
