import inspect
import uuid
from datetime import datetime
from importlib import import_module
from logging.handlers import TimedRotatingFileHandler

import requests
from flask import current_app, Response, request

from lesscode_flask import download_func_dict, SQ_Blueprint
from lesscode_flask.db import db
from lesscode_flask.export_data.data_download_handler import format_to_table_download, upload_result_url
from lesscode_flask.log.access_log_handler import AccessLogHandler
from lesscode_flask.model.response_result import ResponseResult
from lesscode_flask.model.user import User
from lesscode_flask.utils.file.file_utils import check_or_create_dir
from lesscode_flask.utils.helpers import app_config
from lesscode_flask.utils.request.request import sync_get, sync_post
from lesscode_flask.utils.swagger.swagger_template import split_doc
from lesscode_flask.utils.swagger.swagger_util import generate_openapi_spec, replace_symbol, get_params_type, \
    get_sample_data
from lesscode_flask.utils.thread.thread_utils import run_in_background, FlaskThread


# from flask_login import LoginManager
# from flask_swagger_ui import get_swaggerui_blueprint


def setup_logging(app):
    """
    初始化日志配置
    1. 日志等级
        DEBUG : 10
        INFO：20
        WARN：30
        ERROR：40
        CRITICAL：50
    :return:
    """
    import logging
    import sys
    # 日志配置
    # 日志级别
    LOG_LEVEL = app.config.get("LESSCODE_LOG_LEVEL", "DEBUG")
    # 日志格式
    LOG_FORMAT = app.config.get("LESSCODE_LOG_FORMAT",
                                '[%(asctime)s] [%(levelname)s] [%(name)s:%(module)s:%(lineno)d] [%(message)s]')
    # 输出管道
    LOG_STDOUT = app.config.get("LESSCODE_LOG_STDOUT", True)
    # 日志文件备份数量
    LOG_FILE_BACKUPCOUNT = app.config.get("LESSCODE_LOG_FILE_BACKUPCOUNT", 7)
    # 日志文件分割周期
    LOG_FILE_WHEN = app.config.get("LESSCODE_LOG_LOG_FILE_WHEN", "D")
    # 日志文件存储路径
    LOG_FILE_PATH = check_or_create_dir(app.config.get("LESSCODE_LOG_FILE_PATH", 'logs/lesscode.log'))
    formatter = logging.Formatter(LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger().setLevel(LOG_LEVEL.upper())
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout if LOG_STDOUT else sys.stderr)
    console_handler.setFormatter(formatter)
    file_handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE_PATH, when=LOG_FILE_WHEN,
                                                             backupCount=LOG_FILE_BACKUPCOUNT)

    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().addHandler(file_handler)
    logging.addLevelName(100, 'ACCESS')

    LESSCODE_ACCESS_LOG_DB = app.config.get("LESSCODE_ACCESS_LOG_DB", 0)
    if LESSCODE_ACCESS_LOG_DB == 1:
        access_log_handler = AccessLogHandler()
        access_log_handler.level = 100
        logging.getLogger().addHandler(access_log_handler)


def setup_blueprint(app, path=None, pkg_name="handlers", blueprint_map={}):
    import os
    from flask import Blueprint
    import inspect
    """
    动态注册Handler模块
    遍历项目指定包内的Handler，将包内module引入。
    :param path: 项目内Handler的文件路径
    :param pkg_name: 引入模块前缀
    """
    if path is None:
        # 项目内Handler的文件路径，使用当前工作目录作为根
        path = os.path.join(os.getcwd(), pkg_name)
    # 首先获取当前目录所有文件及文件夹
    dynamic_handler_names = os.listdir(path)
    for handler_name in dynamic_handler_names:
        # 利用os.path.join()方法获取完整路径
        full_file = os.path.join(path, handler_name)
        # 循环判断每个元素是文件夹还是文件
        if os.path.isdir(full_file) and handler_name != "__pycache__":
            # 文件夹递归遍历
            setup_blueprint(app, os.path.join(path, handler_name), ".".join([pkg_name, handler_name]), blueprint_map)
        elif os.path.isfile(full_file) and handler_name.lower().endswith("handler.py"):
            # 文件，并且为handler结尾，认为是请求处理器，完成动态装载
            module_path = "{}.{}".format(pkg_name, handler_name.replace(".py", ""))
            module = import_module(module_path)  # __import__(module_path)
            for name, obj in inspect.getmembers(module):
                # 找到Blueprint 的属性进行注册
                if isinstance(obj, Blueprint):
                    # 如果有配置统一前缀则作为蓝图路径的统一前缀
                    blueprint_name = obj.name
                    if blueprint_name in blueprint_map:
                        continue
                    else:
                        if hasattr(obj, "url_prefix") and app.config.get("ROUTE_PREFIX", ""):
                            obj.url_prefix = f'{app.config.get("ROUTE_PREFIX")}{obj.url_prefix}'
                        blueprint_map[blueprint_name] = obj
    return blueprint_map


def setup_query_runner():
    """
    注入数据查询执行器
    :return:
    """
    from redash.query_runner import import_query_runners
    from redash import settings as redash_settings
    import_query_runners(redash_settings.QUERY_RUNNERS)


def setup_sql_alchemy(app):
    """
    配置SQLAlchemy
    :param app:
    :return:
    """
    if app.config.get("SQLALCHEMY_BINDS"):  # 确保配置SQLALCHEMY_BINDS才注册SQLAlchemy
        db.init_app(app)


def setup_login_manager(app):
    try:
        flask_login = import_module("flask_login")
    except ImportError as e:
        raise Exception(f"flask_login is not exist,run:pip install Flask-Login==0.6.3")
    login_manager = flask_login.LoginManager(app)
    setattr(app, "login_manager", login_manager)

    @login_manager.request_loader
    def request_loader(request):
        return User.get_user(request)


def setup_swagger(app):
    """
    配置Swagger
    :param app:
    :return:
    """
    SWAGGER_URL = app.config.get("SWAGGER_URL", "")  # 访问 Swagger UI 的 URL
    # API_URL = 'http://127.0.0.1:5001/static/swagger.json'  # Swagger 规范的路径（本地 JSON 文件）
    API_URL = app.config.get("SWAGGER_API_URL", "")  # 接口
    # 创建 Swagger UI 蓝图
    try:
        flask_swagger_ui = import_module("flask_swagger_ui")
    except ImportError as e:
        raise Exception(f"flask_swagger_ui is not exist,run:pip install flask-swagger-ui==4.11.1")
    swagger_ui_blueprint = flask_swagger_ui.get_swaggerui_blueprint(
        SWAGGER_URL,  # Swagger UI 访问路径
        app.config.get("OUTSIDE_SCREEN_IP") + API_URL,  # Swagger 文件路径
        config={  # Swagger UI 配置参数
            'app_name': "Flask-Swagger-UI 示例"
        }
    )
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

    @app.route(API_URL, methods=['GET'])
    def swagger_spec():
        from lesscode_flask import __version__
        swag = generate_openapi_spec(app, is_read_template=app.config.get("IS_READ_TEMPLATE", True))
        swag['info']['title'] = app.config.get("SWAGGER_NAME", "")
        swag['info']['description'] = app.config.get("SWAGGER_DESCRIPTION", "")
        swag['info']['version'] = app.config.get("SWAGGER_VERSION", __version__)
        return swag


def setup_redis(app):
    redis_conn_list = app.config.get("DATA_SOURCE", [])

    for r in redis_conn_list:
        if r.get("type") == "redis":
            try:
                redis = import_module("redis")
            except ImportError:
                raise Exception(f"redis is not exist,run:pip install redis==5.1.1")
            conn = redis.Redis(host=r.get("host"), port=r.get("port"), db=r.get("db"), password=r.get("password"),
                               decode_responses=True)
            if not hasattr(current_app, "redis_conn_dict"):
                current_app.redis_conn_dict = {}
            if getattr(current_app, "redis_conn_dict").get(r.get("conn_name")):
                raise Exception("Connection {} is repetitive".format(r.get("conn_name")))
            else:
                redis_conn_dict = getattr(current_app, "redis_conn_dict")
                redis_conn_dict.update({
                    r.get("conn_name"): conn
                })
                setattr(current_app, "redis_conn_dict", redis_conn_dict)


def setup_resource_register(app):
    def extract_get_parameters(rule, view_func, param_desc_dict=None):
        if param_desc_dict is None:
            param_desc_dict = {}
        parameters = []
        # 提取查询参数和表单参数
        sig = inspect.signature(view_func)
        for arg, param in sig.parameters.items():
            if arg not in rule.arguments:
                param_info = {
                    "name": arg,
                    "in": "query",
                    "type": "string",
                    "description": param_desc_dict[arg] if param_desc_dict.get(arg) else f"Path parameter {arg}",
                }
                if param.default is inspect.Parameter.empty:
                    param_info["required"] = 1
                    param_info["example"] = get_sample_data(get_params_type(param))
                else:
                    param_info["required"] = 0
                    param_info["default"] = param.default
                    param_info["example"] = param.default
                parameters.append(param_info)
        return parameters

    def extract_post_body(view_func, not_allow_list=None, param_desc_dict=None):
        if param_desc_dict is None:
            param_desc_dict = {}
        param_list = []
        # 提取查询参数和表单参数
        sig = inspect.signature(view_func)
        # 如果_request_type == "json 则是json结构，否则都是form-data结构
        if hasattr(view_func, "_request_type") and view_func._request_type == "urlencoded":
            request_type = "x-www-form-urlencoded"
        elif hasattr(view_func, "_request_type") and view_func._request_type == "form-data":
            request_type = "form-data"
        elif hasattr(view_func, "_request_type") and view_func._request_type == "json-data":
            request_type = "raw"
        else:
            request_type = "raw"
        for arg, param in sig.parameters.items():
            param_info = {
                "name": param.name,
                "type": get_params_type(param),
                "description": param_desc_dict[arg] if param_desc_dict.get(arg) else f"Path parameter {arg}",
                "in": request_type
            }
            # 如果默认值是空，则是必填参数
            if param.default is inspect.Parameter.empty:

                param_info["example"] = get_sample_data(get_params_type(param))
                param_info["required"] = 1
            else:
                param_info["default"] = param.default
                param_info["required"] = 0
                if param.default is not None:
                    param_info["example"] = param.default
                else:
                    param_info["example"] = get_sample_data(get_params_type(param))
            # 如果参数类型是FileStorage 则swagger中format为binary 显示导入文件
            if get_params_type(param) == "FileStorage":
                param_info["format"] = "binary"
            if (not_allow_list and arg not in not_allow_list) or not not_allow_list:
                param_list.append(param_info)

        return param_list

    def extract_path_parameters(rule, param_desc_dict=None):
        if param_desc_dict is None:
            param_desc_dict = {}
        param_list = []
        # 提取路径参数
        for arg in rule.arguments:
            param_list.append({
                "name": arg,
                "in": "path",
                "required": 1,
                "description": param_desc_dict[arg] if param_desc_dict.get(arg) else f"Path parameter {arg}",
                "example": "",
                "default": "",
                "type": "string"
            })
        return param_list

    def convert_to_kebab_case_and_camel_case(input_string):
        # 去掉开头的斜杠
        if input_string.startswith('/'):
            input_string = input_string[1:]
        # 将斜杠替换为下划线
        modified_string = input_string.replace('/', '-')
        # 分割字符串
        parts = modified_string.split('_')
        # 将第一个部分转换为小写，其余部分首字母大写
        camel_case_parts = [parts[0].lower()] + [part.capitalize() for part in parts[1:]]
        # 将所有部分连接成小驼峰格式
        camel_case_string = ''.join(camel_case_parts)
        # 将下划线替换为斜杠
        kebab_case_string = camel_case_string.replace('_', '-')
        return kebab_case_string

    def package_resource(label, symbol, access, type, method="", url="", description="", param_list: list = None):
        """
        :param label: 展示中文名称
        :param symbol: 标识符号
        :param access: 访问权限2：需要权限 1：需要登录 0：游客
        :param type:菜单类型 0：功能分组  1：页面 2：接口 3：前端控件 4：接口池接口
        :param method:post、get
        :param url:接口地址
        :param description:接口描述
        :return:
        """
        symbol = convert_to_kebab_case_and_camel_case(symbol)
        resource = {
            "client_id": current_app.config.get("CLIENT_ID", ""),
            "label": label,
            "symbol": symbol,
            "access": access,
            "type": type,
            "method": method,
            "serial_index": 0,
            "url": url,
            "description": description,
            "is_enable": 1,
            "is_deleted": 0,
            "create_user_id": "-",
            "create_user_name": "-",
            "create_time": str(datetime.now()),
            "param_list": param_list
        }
        return resource

    if current_app.config.get("REGISTER_ENABLE", False) and current_app.config.get("REGISTER_SERVER"):
        resource_list = []
        url_rules_dict = {}
        for blueprint_name, blueprint in app.blueprints.items():
            group_key = f'{blueprint_name}|{blueprint.url_prefix}'
            if blueprint.url_prefix not in ["/swagger-ui"]:
                url_rules_dict[group_key] = []
                # 遍历全局 URL 规则
                for rule in app.url_map.iter_rules():
                    # 筛选出属于当前蓝图的规则
                    if rule.endpoint.startswith(f"{blueprint_name}."):
                        url_rules_dict[group_key].append(rule)

        for parent_resource in url_rules_dict:
            symbol = uuid.uuid1().hex
            label, url = parent_resource.split("|")
            resource = package_resource(label=label, symbol=symbol, url=url, access=0, type=0)
            resource["children"] = []

            for child_resource in url_rules_dict[parent_resource]:
                view_func = app.view_functions[child_resource.endpoint]

                method = list(child_resource.methods - {'HEAD', 'OPTIONS'})[0]
                inter_desc, param_desc_dict, return_desc = split_doc(child_resource, app)
                if method == "POST":
                    path = replace_symbol(child_resource.rule)
                    if "{" in path and "}" in path:
                        path_params = extract_path_parameters(child_resource, param_desc_dict)
                        param_list = extract_post_body(view_func,
                                                       not_allow_list=[param["name"] for param in path_params],
                                                       param_desc_dict=param_desc_dict)
                        param_list = param_list + param_list
                    else:
                        param_list = extract_post_body(view_func, param_desc_dict=param_desc_dict)
                elif method == "GET":
                    param_list = extract_path_parameters(child_resource, param_desc_dict) + extract_get_parameters(
                        child_resource, view_func, param_desc_dict)
                else:
                    param_list = []
                resource["children"].append(
                    package_resource(label=view_func._title, symbol=child_resource.rule, access=1, type=2,
                                     method=method,
                                     url=child_resource.rule,
                                     description=inter_desc, param_list=param_list))
            resource_list.append(resource)
        try:
            httpx = import_module("httpx")
        except ImportError as e:
            raise Exception(f"httpx is not exist,run:pip install httpx==0.24.1")
        with httpx.Client(**{"timeout": None}) as session:
            try:
                res = session.request("post", url=current_app.config.get(
                    "REGISTER_SERVER") + "/icp/authResource/resource_register", json={
                    "resource_list": resource_list
                })
                return res
            except Exception as e:
                raise e


# def setup_static(app):
#     @app.route("/static/<filename>")
#     def static_resource(filename, **kwargs):
#         """
#         方法说明
#         :param download_key:
#         :return:
#         """
#         return send_from_directory('static', filename)

def setup_data_download(app):
    @app.route(f"{current_app.config.get('ROUTE_PREFIX')}/download/data_download", methods=['POST'])
    def data_download(download_key, data_len, params=None, column_list=None, page_size=10, file_name=""):
        """
        方法说明
        :param download_key:
        :return:
        """
        if not file_name:
            file_name = "data_export"
        if not data_len:
            data_len = [1, 1000]
        try:
            offset = data_len[0] - 1
            size = data_len[1] - offset
        except:
            raise Exception("请填写正确的导出条数")
        func = download_func_dict.get(download_key, {})
        request_param = {"offset": offset, "size": size}
        signature = inspect.signature(func)
        for parameter_name, parameter in signature.parameters.items():
            if params.get(parameter_name):
                request_param[parameter_name] = params[parameter_name]
        table_body_list = func(**request_param)
        sta_map_dict = format_to_table_download(table_head_list=column_list, table_body_list=table_body_list)
        url = upload_result_url(sta_map_dict, file_name=file_name)
        return url


def setup_task(app):
    task_routes = SQ_Blueprint("后台任务", url_prefix=f'{app.config.get("ROUTE_PREFIX", "")}')

    @task_routes.post_route(f"运行任务", methods=['POST'])
    def task_run(func_key: str, task_params: dict = None):
        print(request.headers)
        module, qualname = func_key.split(":")
        m = import_module(module)
        func = m
        if "." in qualname:
            tmp = qualname.split(".")
            for t in tmp:
                func = getattr(func, t)
        else:
            func = getattr(m, qualname)
        task_params = task_params or dict()
        run_in_background([FlaskThread(target=func, args=[], kwargs=task_params)])

    app.register_blueprint(task_routes)


def setup_scheduler(app):
    if current_app.config.get("SCHEDULER_ENABLE", False):
        try:
            flask_apscheduler = import_module("flask_apscheduler")
        except ImportError as e:
            raise Exception(f"flask_apscheduler is not exist,run:pip install flask_apscheduler==1.13.1")
        scheduler = flask_apscheduler.APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        task_list = current_app.config.get("SCHEDULER_TASK_LIST", [])
        if task_list:
            for task in task_list:
                if isinstance(task, dict):
                    task_func = task.get("task_func")
                    func_kwargs = task.get("func_kwargs", {}) or dict()
                    task_enable = task.get("enable", False)
                    task_kwargs = task.get("task_kwargs", {}) or dict()
                    if task_enable:
                        scheduler.add_job(func=task_func, kwargs=func_kwargs, **task_kwargs)


def setup_common_resource(app):
    routes = SQ_Blueprint("Oauth授权管理", url_prefix=f'{app.config.get("ROUTE_PREFIX", "")}/oauth')

    auth_menu_routes = SQ_Blueprint("菜单管理", url_prefix=f'{app.config.get("ROUTE_PREFIX", "")}/authMenu')

    def capacity_post(path, data=None, headers=None, result_type="json", pack=False, **kwargs):
        res = sync_post(path=path, data=data, base_url=f'{app_config.get("CAPABILITY_PLATFORM_SERVER")}/icp',
                        headers=headers, result_type=result_type, pack=pack, **kwargs)
        return res

    def capacity_get(path, params=None, result_type="json", headers=None, pack=False, **kwargs):
        res = sync_get(path=path, params=params, base_url=f'{app_config.get("CAPABILITY_PLATFORM_SERVER")}/icp',
                       headers=headers, result_type=result_type, pack=pack, **kwargs)
        return res

    @routes.get_route("获取图形验证码", '/captcha')
    def get_captcha(key):
        resp = requests.get(app_config.get("CAPABILITY_PLATFORM_SERVER") + "/icp/oauth/captcha", params={
            "key": key
        }, stream=True)
        return Response(
            resp.content,
            content_type=resp.headers["Content-Type"],
            status=resp.status_code
        )

    @routes.post_route("登录", '/token')
    def issue_token():
        """
        获取token
        :return:
        """
        form_data = request.form.to_dict()

        # 获取请求头并删除不必要的字段（如 Host）
        headers = {key: value for key, value in request.headers if key.lower() in ["authorization"]}
        files = []
        response = requests.request("POST", app_config.get("CAPABILITY_PLATFORM_SERVER") + "/icp/oauth/token", headers=headers,
                                    data=form_data, files=files)

        # 返回 B 项目的响应
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )

    @routes.get_route("登出接口", '/logout')
    def logout():
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}

        result = capacity_get("/oauth/logout", headers=headers)

        return result

    @routes.get_route("获取短信验证码", '/sms')
    def get_sms_code(phone_no: str):
        """
        发送短信验证码
        :param sign_name:
        :param template_code:
        :param phone_no:手机号
        :return:
        """
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}
        template_code = app_config.get("ICP_RESOURCE_PROXY_SMS_TEMPLATE_CODE")
        sign_name = app_config.get("SMS_TEMPLATE").get(template_code, {}).get("sign_name")
        result = capacity_get("/oauth/sms", headers=headers, params={
            "phone_no": phone_no,
            "template_code": template_code,
            "sign_name": sign_name,
        })
        return result

    @routes.get_route('获取当前用户信息', '/user_info')
    def user_info():
        """
        获取当前用户信息
        :return:
        """
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}

        result = capacity_get("/oauth/user_info", headers=headers)

        return result

    @routes.post_route("微信mini的code2session", )
    def wx_mini_code2session(js_code, client_id=None, app_id=None):
        """
        微信mini的code2session
        :param js_code: 微信小程序授权码
        :param client_id:应用id
        :param app_id:微信应用id
        :return:
        """
        headers = {key: value for key, value in request.headers if key.lower() in ["authorization"]}

        result = capacity_post("/third_service_user/wx_mini_code2session", headers=headers, data={
            "js_code": js_code,
            "client_id": client_id,
            "app_id": app_id,
        }, pack=True)
        if result.get("status") == "00000":
            return result.get("data")
        else:
            ResponseResult.fail(data=result.get("data"), message=f'{result.get("message", "未知错误")}',
                                status_code=result.get("status"))

    @routes.get_route("微信mini的code2session", )
    def wx_mini_code2session_v2(js_code, service_id: str):
        """
                微信mini的code2session
                :param js_code: 微信小程序授权码
                :param service_id: 三方服务表里的id
                :return:
                """
        headers = {key: value for key, value in request.headers if key.lower() in ["authorization"]}

        result = capacity_post("/third_service_user/wx_mini_code2session_v2", headers=headers, data={
            "js_code": js_code,
            "service_id": service_id
        }, pack=True)
        if result.get("status") == "00000":
            return result.get("data")
        else:
            ResponseResult.fail(data=result.get("data"), message=f'{result.get("message", "未知错误")}',
                                status_code=result.get("status"))

    @routes.post_route("微信mini的用户信息解密")
    def wx_mini_userinfo_decrypt(app_id, session_key, iv, encrypted_data):
        """
        微信mini的用户信息解密
        :param app_id:
        :param session_key:
        :param iv:
        :param encrypted_data:
        :return:
        """
        headers = {key: value for key, value in request.headers if key.lower() in ["authorization"]}
        result = capacity_post("/third_service_user/wx_mini_userinfo_decrypt", headers=headers, data={
            "app_id": app_id,
            "session_key": session_key,
            "iv": iv,
            "encrypted_data": encrypted_data,
        },
                               pack=True)
        if result.get("status") == "00000":
            return result.get("data")
        else:
            ResponseResult.fail(data=result.get("data"), message=f'{result.get("message", "未知错误")}',
                                status_code=result.get("status"))

    @routes.post_route("通过auth_code获取专有钉钉用户信息")
    def get_proper_ding_user_info_by_auth_code(client_id, app_id, auth_code):
        headers = {key: value for key, value in request.headers if key.lower() in ["authorization"]}
        result = capacity_post("/third_service_user/get_proper_ding_user_info_by_auth_code", headers=headers,
                               data={
                                   "client_id": client_id,
                                   "app_id": app_id,
                                   "auth_code": auth_code,
                               }, pack=True)
        if result.get("status") == "00000":
            return result.get("data")
        else:
            ResponseResult.fail(data=result.get("data"), message=f'{result.get("message", "未知错误")}',
                                status_code=result.get("status"))

    @routes.post_route("通过临时授权码code获取专有钉钉用户信息")
    def get_proper_ding_user_info_by_code(client_id, app_id, code):
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}
        result = capacity_post("/third_service_user/get_proper_ding_user_info_by_code", headers=headers,
                               data={
                                   "client_id": client_id,
                                   "app_id": app_id,
                                   "code": code,
                               }, pack=True)
        if result.get("status") == "00000":
            return result.get("data")
        else:
            ResponseResult.fail(data=result.get("data"), message=f'{result.get("message", "未知错误")}',
                                status_code=result.get("status"))
        return result

    @routes.post_route('微信扫码获取微信用户信息', '/get_wx_user_info_by_code')
    def get_wx_user_info_by_code(code: str, state: str):
        """
        对应微信的临时授权码获取用户信息
        :param state: 三方服务表里的id
        :param code:微信扫码的临时授权码
        :return:
        """
        headers = {key: value for key, value in request.headers if key.lower() in ["authorization"]}

        result = capacity_post("/third_service_user/get_wx_user_info_by_code", headers=headers, data={
            "code": code,
            "state": state,
        }, pack=True)

        if result.get("status") == "00000":
            return result.get("data")
        else:
            ResponseResult.fail(data=result.get("data"), message=f'{result.get("message", "未知错误")}',
                                status_code=result.get("status"))

    @routes.post_route('绑定三方信息', '/bind_by_third_user_info')
    def bind_by_third_user_info(user_id: str, service_id: str, open_id: str = None, union_id: str = None,
                                password: str = None, third_user_info: dict = None):
        """
        绑定三方信息
        :param user_id: 上奇用户id
        :param service_id: 三方表id
        :param open_id: 三方服务的用户id
        :param union_id:三方服务的用户的统一id
        :param password: 密码
        :param third_user_info: 三方基本信息
        :return:
        """
        headers = {key: value for key, value in request.headers if key.lower() in ["authorization"]}

        result = capacity_post("/authUser/bind_by_third_user_info", headers=headers, data={
            "user_id": user_id,
            "service_id": service_id,
            "open_id": open_id,
            "union_id": union_id,
            "password": password,
            "third_user_info": third_user_info
        }, pack=True)

        if result.get("status") == "00000":
            return result.get("data")
        else:
            ResponseResult.fail(data=result.get("data"), message=f'{result.get("message", "未知错误")}',
                                status_code=result.get("status"))

    @routes.post_route('解绑三方信息', '/unbind')
    def unbind(user_id: str, service_type: str, open_id: str = None, union_id: str = None, ):
        """
        绑定三方信息
        :param user_id: 上奇用户id
        :param service_type: 绑定类型
        :param open_id: 三方服务的用户id
        :param union_id:三方服务的用户的统一id
        :return:
        """
        headers = {key: value for key, value in request.headers if key.lower() in ["authorization"]}

        result = capacity_post("/authUser/unbind", headers=headers, data={
            "service_type": service_type,
            "user_id": user_id,
            "open_id": open_id,
            "union_id": union_id,
        }, pack=True)

        if result.get("status") == "00000":
            return result.get("data")
        else:
            ResponseResult.fail(data=result.get("data"), message=f'{result.get("message", "未知错误")}',
                                status_code=result.get("status"))

    @auth_menu_routes.post_route('查询用户菜单', '/get_menu')
    def get_menu():
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}

        result = capacity_post("/authMenu/get_menu", headers=headers)

        return result

    # 判断是否需要代理资源
    if app_config.get("ICP_RESOURCE_PROXY"):
        app.register_blueprint(routes)
        app.register_blueprint(auth_menu_routes)
