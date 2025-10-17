# -*- coding: utf-8 -*-
import json
from datetime import datetime

from flask import Response, abort


class ResponseResult(dict):
    """
    ResponseResult 类用于统一包装数据返回格式
    """

    def __init__(self, status_code=("00000", "请求成功"), data=""):
        """

        :param status_code:
        :param data:
        """
        super(ResponseResult, self).__init__()
        # 业务请求状态编码
        self["status"] = status_code[0]
        # 返回状态码对应的说明信息
        self["message"] = status_code[1]
        # 返回数据对象 主对象 指定类型
        self["data"] = data
        # 时间戳
        self["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    @staticmethod
    def make_response(message: str, data="", status_code="00000", http_code=200):
        data = json.dumps(ResponseResult(status_code=(status_code, message), data=data))
        respone = Response(data)
        respone.content_type = "application/json"
        respone.status_code = http_code
        return respone

    @staticmethod
    def success(data, message: str = None):
        """
        成功返回结果
        :param data:
        :param message:
        :return:
        """
        if message:
            return ResponseResult(data=data, status_code=("00000", message))
        return ResponseResult(data=data)

    @staticmethod
    def fail(message: str, data="", status_code="99999", http_code=200):
        """
        失败返回结果
        :param message:
        :param data:
        :param status_code:
        :param http_code:
        :return:
        """
        if len(message) > 100:
            message = "服务器内部错误,请联系管理员排查"
        respone = ResponseResult.make_response(message, data, status_code, http_code)
        abort(respone)
