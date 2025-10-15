#!/usr/bin/python
# -*- coding: UTF-8 -*-

class BaseRequest:
    """请求类的父类"""

    biz_model = {}
    """请求参数"""

    params_model = {}
    """url携带参数(GET请求以外有效)"""

    files = None
    """上传文件"""

    def __init__(self):
        pass

    def get_method(self):
        """返回接口名

        :return: 返回接口名
        :rtype: str
        """
        raise Exception('未实现BaseRequest.get_method()方法')

    def get_version(self):
        """返回接口版本号

        :return: 返回版本号，如：1.0
        :rtype: str
        """
        return '1.0'

    def get_sdk_version(self):
        """返回sdk版本号

        :return: 返回sdk版本号，如：1.0
        :rtype: str
        """
        return '1.0'

    def get_request_type(self):
        """返回请求类型

        :return: 返回RequestType类实例
        :rtype:  common.RequestType
        """
        raise Exception('未实现BaseRequest.get_request_type()方法')

