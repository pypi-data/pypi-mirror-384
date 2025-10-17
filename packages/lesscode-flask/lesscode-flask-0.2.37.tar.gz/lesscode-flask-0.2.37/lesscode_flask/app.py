from __future__ import annotations

import copy
import json
import logging
import os
import sys
import time
import traceback
import typing as t

from flask import Flask, typing as ft, Response
from flask.globals import request_ctx, request
from flask_login import current_user
from lesscode_utils.json_utils import JSONEncoder
from werkzeug.middleware.proxy_fix import ProxyFix

from lesscode_flask.model.response_result import ResponseResult
from lesscode_flask.setup import setup_blueprint, setup_logging, setup_query_runner, setup_swagger, setup_sql_alchemy, \
    setup_redis, setup_login_manager, setup_resource_register, setup_data_download, setup_scheduler, \
    setup_common_resource, setup_task
from lesscode_flask.signals import app_runed
from lesscode_flask.utils.decorator.sql_injection import contains_sql_injection
from lesscode_flask.utils.helpers import inject_args, generate_uuid, app_config
from lesscode_flask.utils.json.NotSortJSONProvider import NotSortJSONProvider
from lesscode_flask.utils.limit import RedisRateLimiter
from lesscode_flask.utils.limit.consecutive.consecutive_limiter_handler import ConsecutiveAccessLimitHandler
from lesscode_flask.utils.limit.consecutive.redis_consecutive_limiter import RedisConsecutiveAccessLimiter
from lesscode_flask.utils.limit.limit_util import get_rate_limit_info, get_count_limit_info, get_user_limit_policy
from lesscode_flask.utils.limit.req.rate_limiter_handler import RateLimitHandler
from lesscode_flask.utils.limit.req_count.count_limiter_handler import CountLimitHandler
from lesscode_flask.utils.limit.req_count.redis_count_limiter import RedisCountLimiter
from lesscode_flask.utils.redis.redis_helper import RedisHelper
from lesscode_flask.utils.swagger.swagger_util import generate_openapi_spec

# import collections.abc as cabc


class Lesscoder(Flask):
    """A custom Flask app for lesscode-flask"""

    def __init__(self, *args, **kwargs):
        # kwargs.update(
        #     {
        #         "template_folder": settings.FLASK_TEMPLATE_PATH,
        #         "static_folder": settings.STATIC_ASSETS_PATH,
        #         "static_url_path": "/static",
        #     }
        # )
        super(Lesscoder, self).__init__(__name__, *args, **kwargs)
        # Make sure we get the right referral address even behind proxies like nginx.
        # 将self.wsgi_app设置为一个经过ProxyFix包装的应用程序。
        # ProxyFix配置为信任代理服务器发来的X - Forwarded - For和X - Host头部信息，各信任一层（即数值1）。
        # 这里的ProxyFix通常用于修复在反向代理环境下WSGI应用收到的客户端地址和主机头信息。
        self.wsgi_app = ProxyFix(self.wsgi_app, x_for=1, x_host=1)
        # # Configure Redash using our settings
        profile_list = [item for item in sys.argv if item.__contains__("--profile=")]
        if profile_list:  # 如果有指定配置文件，更新参数，如果指定多次，取最后一次
            profile = profile_list[-1].replace('--profile=', '')
            setting_name = "setting.config_{}.Config".format(profile)
        else:
            setting_name = "setting.config.Config"
        self.config.from_object(setting_name)
        self.register_error_handler(Exception, self.handle_exception)
        REDIS_RATE_LIMIT_ENABLE = self.config.get("RATE_LIMIT_ENABLE", False)
        if REDIS_RATE_LIMIT_ENABLE:
            self.rateLimiter = RedisRateLimiter(self.config.get("REDIS_LIMIT_KEY", "redis"))
        REDIS_COUNT_LIMIT_ENABLE = self.config.get("COUNT_LIMIT_ENABLE", False)
        if REDIS_COUNT_LIMIT_ENABLE:
            self.countLimiter = RedisCountLimiter(self.config.get("REDIS_LIMIT_KEY", "redis"))

        REDIS_CONSECUTIVE_LIMIT_ENABLE = self.config.get("CONSECUTIVE_ACCESS_LIMIT_ENABLE", False)
        if REDIS_CONSECUTIVE_LIMIT_ENABLE:
            self.consecutiveAccessLimiter = RedisConsecutiveAccessLimiter(self.config.get("REDIS_LIMIT_KEY", "redis"))

    def preprocess_request(self) -> ft.ResponseReturnValue | None:
        v = super(Lesscoder, self).preprocess_request()
        user_limit_policy = None
        if  hasattr(self, 'countLimiter') and self.countLimiter:
            if not user_limit_policy:
                user_limit_policy = get_user_limit_policy()
            allowed, remaining = self.countLimiter.is_allowed(user_limit_policy)
            if not allowed:
                countLimitHandler =  self.config.get("COUNT_LIMIT_HANDLER", CountLimitHandler)
                countLimitHandler(request,remaining).response_handler()
        if  hasattr(self, 'rateLimiter') and self.rateLimiter:
            if not user_limit_policy:
                user_limit_policy = get_user_limit_policy()
            #  是否触发限流 延迟时间 超出数量
            allowed,delay, excess =  self.rateLimiter.is_limited(user_limit_policy)
            if not allowed :
                rateLimitHandler = self.config.get("RATE_LIMIT_HANDLER", RateLimitHandler)
                rateLimitHandler(request,delay, excess).response_handler()

        if  hasattr(self, 'consecutiveAccessLimiter') and self.consecutiveAccessLimiter:
            if not user_limit_policy:
                user_limit_policy = get_user_limit_policy()
            #  是否触发限流 延迟时间 超出数量
            allowed,current_count =  self.consecutiveAccessLimiter.is_allowed(user_limit_policy)
            if not allowed :
                consecutiveAccessLimiter = self.config.get("CONSECUTIVE_ACCESS_LIMIT_HANDLER", ConsecutiveAccessLimitHandler)
                consecutiveAccessLimiter(request,current_count).response_handler()
        if self.config.get("AUTHORIZATION_ENABLE"):  # 启动 AUTHORIZATION_ENABLE 才进行权限验证
            # 获取当前请求的url
            url = request.path
            # 获取URL 对应的标识符 与访问权限
            symbol, access = RedisHelper(app_config.get("REDIS_OAUTH_KEY", "redis")).sync_hmget(f"upms:url_info:{url}",
                                                                                                ["symbol", "access"])
            if not symbol:
                # 如果没有进行注册的url 默认需要登录权限
                access = app_config.get("AUTH_DEFAULT_ACCESS", "0")
            # '访问权限2：需要权限 1：需要登录 0：游客',
            if str(access) == "1":  # 需要登录
                if current_user.is_anonymous_user:
                    # abort(403, "需要登录")
                    ResponseResult.fail("请登录后访问", status_code="401", http_code="401")
            elif str(access) == "2":  # 需要权限
                if current_user.is_anonymous_user:
                    ResponseResult.fail("请登录后访问", status_code="401", http_code="401")
                if not current_user.has_permission(url):
                    ResponseResult.fail("请获取授权后访问", status_code="403", http_code="403")
        return v

    def full_dispatch_request(self) -> Response:
        # 生成请求标识
        request_id = request.headers.get('Request-Id')
        if request_id is None:
            request_id = generate_uuid()
        # 设置请求标识
        request.request_id = request_id
        start_time = time.time()
        response = super(Lesscoder, self).full_dispatch_request()
        # 为响应设置请求标识
        response.headers['Request-Id'] = request_id
        # # 计算请求耗时
        # duration = time.time() - start_time
        # 100 为自定义 'ACCESS' 的日志级别标识
        logging.log(100, "访问日志", {"request_id": request_id, "start_time": start_time, "end_time": time.time(),
                                      "status_code": response.status_code})
        return response

    def dispatch_request(self) -> ft.ResponseReturnValue:
        """
            实现参数自动注入功能，对父级代码进行重写
        """
        # 此处开始  均为原代码直接拷贝
        req = request_ctx.request
        if req.routing_exception is not None:
            self.raise_routing_exception(req)
        rule: Rule = req.url_rule  # type: ignore[assignment]
        # if we provide automatic options for this URL and the
        # request came with the OPTIONS method, reply automatically
        if (
                getattr(rule, "provide_automatic_options", False)
                and req.method == "OPTIONS"
        ):
            return self.make_default_options_response()
        # otherwise dispatch to the handler for that endpoint
        view_args: dict[str, t.Any] = req.view_args  # type:
        func = self.view_functions[rule.endpoint]
        # 到此结束 以下增加新实现
        # 此处增加参数注入代码
        params_dict = inject_args(req, func, view_args)
        params_dict.update(view_args)
        SQL_INJECTION_ENABLE = self.config.get("SQL_INJECTION_ENABLE", False)
        if SQL_INJECTION_ENABLE:
            if contains_sql_injection(params_dict):
                ResponseResult.fail("参数包含非法字符，请调整后重试！", status_code="403", http_code="403")
        # 调用处理函数执行请求处理
        result = self.ensure_sync(func)(**params_dict)
        # 获取不包装路径
        NOT_RESPONSE_RESULT = self.config.get("NOT_RESPONSE_RESULT", [])
        # 如果访问的路径以不包装路径开头，则不包装返回结果
        for url in NOT_RESPONSE_RESULT:
            if req.full_path.startswith(url):
                return result
        try:
            # 判断返回结构是否是json，不是json则不包装
            json.dumps(result, cls=JSONEncoder, ensure_ascii=False)
            return ResponseResult(data=result)
        except Exception as e:
            print(e)
            return result

    def setup(self):
        setup_logging(self)
        blueprint_map = setup_blueprint(self)
        setup_query_runner()
        setup_swagger(self)
        setup_sql_alchemy(self)
        setup_redis(self)
        setup_login_manager(self)
        for blueprint_name, blueprint in blueprint_map.items():
            self.register_blueprint(blueprint)
        setup_common_resource(self)
        setup_resource_register(self)
        setup_data_download(self)
        setup_scheduler(self)
        setup_task(self)

    #  setup_static(self)

    @staticmethod
    def handle_exception(e):
        traceback.print_exc()  # 打印堆栈信息
        # 统一异常处理
        if hasattr(e, "get_response"):
            response = e.get_response()
            return ResponseResult.make_response(message=e.description, data=f"{e.code} {e.name}",
                                                http_code=response.status_code, status_code="500")
        else:
            return ResponseResult.make_response(message=str(e), data=str(e), http_code=500, status_code="500")


def gen_swagger_json_file(app):
    swagger_json = generate_openapi_spec(app)
    _port = app.config.get("PORT") or 5004
    _swagger_json = copy.deepcopy(swagger_json)
    _swagger_json["servers"] = app.config.get("SWAGGER_SERVERS", []) if app.config.get("SWAGGER_SERVERS", []) else [
        {"url": f"http://127.0.0.1:{_port}", "description": "本地环境"}]
    project_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    static_path = os.path.join(project_path, "static")
    swagger_json_path = os.path.join(static_path, "swagger.json")
    if not os.path.exists(static_path):
        os.mkdir(static_path)
    if not os.path.exists(swagger_json_path):
        with open(swagger_json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(_swagger_json, indent=4, ensure_ascii=False))


from flask import current_app


def create_app():
    app = Lesscoder()
    app_config.config(app)
    app.json = NotSortJSONProvider(app)  # 设置自定义的 JSON provider
    with app.app_context():
        app.setup()
        # 发送 app_runed 信号
        app_runed.send(current_app)
    gen_swagger_json_file(app)
    return app
