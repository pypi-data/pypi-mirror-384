import hashlib

from flask import request, current_app

from lesscode_flask.model.user import flask_login
from lesscode_flask.model.user_limit_policy import UserLimitPolicy
from lesscode_flask.utils.helpers import app_config
from lesscode_flask.utils.redis.redis_helper import RedisHelper


def limit_key_encode() -> str:
    limit_key = None
    # 白名单
    limit_white_list = app_config.get("LIMIT_WHITE_LIST", [])
    request_url = request.path
    if request_url in limit_white_list:
        # 白名单访问 直接返回None
        return None
    # 1、获取当前用户
    current_user = flask_login.current_user
    if current_user and not current_user.is_anonymous_user:
        user_id = current_user.id
        # 拼接 key 用户id+url
        limit_key = f"{user_id}:{request_url}"
    # 如果键为空，使用客户端IP
    if not limit_key:
        limit_key = f"{request.remote_addr}{request_url}"
    # 对键进行哈希处理，避免键过长
    limit_key = hashlib.md5(limit_key.encode('utf-8')).hexdigest()
    return hashlib.md5(limit_key.encode('utf-8')).hexdigest()

def limit_key(request_url) -> str:
    """
    构建访问计数信息的redis 缓存key
    :param request_url:
    :return:
    """
    limit_key = None
    # 1、获取当前用户
    current_user = flask_login.current_user
    if current_user and not current_user.is_anonymous_user:
        user_id = current_user.id
        # 拼接 key 用户id+url
        limit_key = f"{user_id}:{request_url}"
    # 如果键为空，使用客户端IP
    if not limit_key:
        limit_key = f"{request.remote_addr}{request_url}"
    # 对键进行哈希处理，避免键过长
    limit_key = hashlib.md5(limit_key.encode('utf-8')).hexdigest()
    return limit_key

def get_rate_limit_info() -> str:
    """
    获取限流信息，包含限流key 频率 rate , 突发数量 burst:
    :return: 实际使用的限流键
    """
    rate = app_config.get("RATE_LIMIT_RATE", 1)  # 限流频率 单位是每秒
    burst = app_config.get("RATE_LIMIT_BURST", 0)  # 限流频率允许的突发值 请求速率超过（rate + brust）的请求会被直接拒绝。
    time_window = app_config.get("RATE_LIMIT_TIME_WINDOW", 1)  # 限流频率允许的突发值 请求速率超过（rate + brust）的请求会被直接拒绝。
    limit_key = limit_key_encode()
    return limit_key, rate, burst,time_window

def get_count_limit_info() -> str:
    """
    获取限流信息，包含限流key 总量 rate , 窗口期 burst:
    :return: 实际使用的限流键
    """
    # 窗口期内最大访问量
    count = app_config.get("COUNT_LIMIT_COUNT",500)
    # 窗口期时长 单位秒
    time_window = app_config.get("COUNT_LIMIT_TIME_WINDOW",3600)
    limit_key = limit_key_encode()
    user_limit_policy = get_user_limit_policy()
    return limit_key, count, time_window


def get_user_limit_policy():
    limit_policy_id = None  # 初始化变量
    user_limit_policy = None  # 初始化变量
    REDIS_OAUTH_KEY = app_config.get("REDIS_OAUTH_KEY", "redis")

    # 1、获取当前用户
    current_user = flask_login.current_user
    if current_user and not current_user.is_anonymous_user:
        limit_policy_id = current_user.limit_policy
        # item["white_list"] = json.dumps(item.get("white_list", []))
    if limit_policy_id:
        key = f"limit_policy:{limit_policy_id}"
        limit_policy_id = RedisHelper(REDIS_OAUTH_KEY).sync_hgetall(key)
        user_limit_policy = UserLimitPolicy(**limit_policy_id)

    if user_limit_policy:
        return user_limit_policy
    else:
        # 如果没有策略就构建默认策略
        REDIS_RATE_LIMIT_ENABLE = app_config.get("RATE_LIMIT_ENABLE", False)
        REDIS_COUNT_LIMIT_ENABLE = app_config.get("COUNT_LIMIT_ENABLE", False)
        CONSECUTIVE_ACCESS_LIMIT_ENABLE = app_config.get("CONSECUTIVE_ACCESS_LIMIT_ENABLE", False)
        LIMIT_WHITE_LIST = app_config.get("LIMIT_WHITE_LIST", False)
        return UserLimitPolicy(rate_limit_enable=int(REDIS_RATE_LIMIT_ENABLE),consecutive_limit_enable=int(CONSECUTIVE_ACCESS_LIMIT_ENABLE),
                               count_limit_enable=int(REDIS_COUNT_LIMIT_ENABLE),white_list=LIMIT_WHITE_LIST)

