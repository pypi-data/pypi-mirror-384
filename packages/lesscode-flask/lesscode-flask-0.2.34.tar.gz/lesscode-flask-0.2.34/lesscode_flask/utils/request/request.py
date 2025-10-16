import importlib
import uuid

from flask.globals import request as flask_request

from lesscode_flask.model.response_result import ResponseResult
from lesscode_flask.utils.helpers import app_config


def get_basic_auth(username, password):
    try:
        httpx = importlib.import_module("httpx")
    except ImportError as e:
        raise Exception(f"httpx is not exist,run:pip install httpx==0.24.1")
    return httpx.BasicAuth(username, password)


def sync_common_request_origin(url, method, params=None, data=None, json=None, connect_config=None,
                               **kwargs):
    if not connect_config or not isinstance(connect_config, dict):
        connect_config = {"timeout": None}
    try:
        httpx = importlib.import_module("httpx")
    except ImportError as e:
        raise Exception(f"httpx is not exist,run:pip install httpx==0.24.1")
    with httpx.Client(**connect_config) as session:
        try:
            res = session.request(method.upper(), url=url, params=params, data=data, json=json, **kwargs)
            return res
        except Exception as e:
            raise e


def sync_common_request(method, path, params=None, data=None, json=None, base_url=None, result_type="json",
                        pack=False, connect_config=None, **kwargs):
    if not base_url:
        base_url = app_config.get("CAPABILITY_PLATFORM_SERVER", "")
    headers = kwargs.get("headers", {}) or {}
    if not headers.get("Request-Id"):
        headers["Request-Id"] = uuid.uuid1().hex

    request_id = flask_request.request_id
    if request_id:
        headers["Request-Id"] = request_id
    elif not headers.get("Request-Id"):
        headers["Request-Id"] = uuid.uuid1().hex
    if not headers.get("Project-Name"):
        project_name = app_config.get("PROJECT_NAME", "").encode("utf-8")
        headers["Project-Name"] = project_name
    kwargs["headers"] = headers
    try:
        res = sync_common_request_origin(url=base_url + path, method=method.upper(), params=params, data=data,
                                         json=json, connect_config=connect_config, **kwargs)
        if result_type == "json":
            res = res.json()
            if not pack:
                if res.get("status") == "00000":
                    res = res.get("data")
                else:
                    # message = f'ori_message:{res.get("status", "")}, {res.get("message", "未知错误")}'
                    # abort("500", message)
                    ResponseResult.fail(data=res.get("data"), message=f'{res.get("message", "未知错误")}')
        elif result_type == "text":
            res = res.text
        elif result_type == "origin":
            return res
        else:
            res = res.content
        return res
    except Exception as e:
        raise e


def sync_get(path, params=None, base_url=None, result_type="json", pack=False, connect_config=None, **kwargs):
    if connect_config is None:
        connect_config = app_config.get("CONNECT_CONFIG", {})
    res = sync_common_request(method="GET", path=path, params=params, base_url=base_url,
                              result_type=result_type, pack=pack, connect_config=connect_config, **kwargs)
    return res


def sync_post(path, data=None,
              base_url=None,
              result_type="json", pack=False, connect_config=None, **kwargs):
    flag = kwargs.pop("flag", True)
    if connect_config is None:
        connect_config = app_config.get("CONNECT_CONFIG", {})
    if flag:
        res = sync_common_request(method="POST", path=path, json=data, base_url=base_url,
                                  result_type=result_type, pack=pack, connect_config=connect_config, **kwargs)
        return res
    else:
        res = sync_common_request(method="POST", path=path, data=data, base_url=base_url,
                                  result_type=result_type, pack=pack, connect_config=connect_config, **kwargs)
        return res


def sync_patch(path, params=None, data=None, json=None, base_url=None,
               result_type="json", pack=False, connect_config=None, **kwargs):
    if connect_config is None:
        connect_config = app_config.get("CONNECT_CONFIG", {})
    res = sync_common_request(method="PATCH", path=path, params=params, data=data, json=json, base_url=base_url,
                              result_type=result_type, pack=pack, connect_config=connect_config, **kwargs)
    return res


def sync_put(path, params=None, data=None, json=None, base_url=None,
             result_type="json", pack=False, connect_config=None, **kwargs):
    if connect_config is None:
        connect_config = app_config.get("CONNECT_CONFIG", {})
    res = sync_common_request(method="PATCH", path=path, params=params, data=data, json=json, base_url=base_url,
                              result_type=result_type, pack=pack, connect_config=connect_config, **kwargs)
    return res


def sync_delete(path, params=None, data=None, json=None, base_url=None,
                result_type="json", pack=False, connect_config=None, **kwargs):
    if connect_config is None:
        connect_config = app_config.get("CONNECT_CONFIG", {})
    res = sync_common_request(method="DELETE", path=path, params=params, data=data, json=json, base_url=base_url,
                              result_type=result_type, pack=pack, connect_config=connect_config, **kwargs)
    return res
