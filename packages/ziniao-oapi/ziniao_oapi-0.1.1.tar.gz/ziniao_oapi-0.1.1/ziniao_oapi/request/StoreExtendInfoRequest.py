#!/usr/bin/python
# -*- coding: UTF-8 -*-
from ziniao_oapi.common import RequestTypes
from ziniao_oapi.request.BaseRequest import BaseRequest


class StoreExtendInfoRequest(BaseRequest):
    """获取店铺扩展信息请求"""

    def __init__(self):
        BaseRequest.__init__(self)

    def get_method(self):
        return '/store/get_extend_info'

    def get_version(self):
        return '1.0'

    def get_request_type(self):
        return RequestTypes.POST_JSON
