# 装饰器来标识请求类型
from functools import wraps


def request_type(content_type="json"):
    """
    :param content_type: form-data,json,urlencoded
    :return:
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)

        decorated_function._request_type = content_type
        return decorated_function

    return decorator
