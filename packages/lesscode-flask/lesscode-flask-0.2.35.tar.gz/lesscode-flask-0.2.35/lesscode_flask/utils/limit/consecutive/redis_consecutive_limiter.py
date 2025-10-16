import logging
from flask import request

from lesscode_flask.model.user import flask_login
from lesscode_flask.model.user_limit_policy import UserLimitPolicy
from lesscode_flask.utils.redis.redis_helper import RedisHelper

logger = logging.getLogger(__name__)

class RedisConsecutiveAccessLimiter:
    """Redis连续访问限流器实现"""

    def __init__(self, redis_key):
        self.redis_key = redis_key

    def is_allowed(self, user_limit_policy: UserLimitPolicy):
        """
        检查是否允许请求（限制用户连续访问同一路径）
        :return: (allowed, current_count)
        """
        consecutive_limit_count = user_limit_policy.consecutive_limit_count
        consecutive_limit_enable = user_limit_policy.consecutive_limit_enable
        limit_white_list = user_limit_policy.white_list

        request_url = request.path

        # 未启用连续访问限制 或者 在白名单中 直接返回允许
        if consecutive_limit_enable == 0 or request_url in limit_white_list:
            return True, 0

        # 限流键 (包含用户标识和请求路径)
        limit_key = None
        # 1、获取当前用户
        current_user = flask_login.current_user
        if current_user and not current_user.is_anonymous_user:
            # 拼接 key 用户id
            limit_key = current_user.id
        # 如果键为空，使用客户端IP
        if not limit_key:
            limit_key = f"{request.remote_addr}"
        limit_key = f"{limit_key}"
        key = f"limit_consecutive:{limit_key}:{request_url}"

        try:
            # 获取当前连续访问次数
            current_count_str = RedisHelper(self.redis_key).sync_get(key)


            if current_count_str is None:
                keys = RedisHelper(self.redis_key).sync_keys(f"limit_consecutive:{limit_key}:*")
                RedisHelper(self.redis_key).sync_delete(keys)

                # 第一次访问，设置计数为1
                current_count = 1
                RedisHelper(self.redis_key).sync_set(key, current_count, 3600)  # 默认保存1小时
            else:
                # current_count = int(current_count_str) + 1
                # 增加连续访问计数
                current_count =  RedisHelper(self.redis_key).sync_incrby(name=key, amount=1)

            # 检查是否超过限制
            if current_count >= consecutive_limit_count:
                # 超过限制
                return False, current_count
            else:
                return True, current_count

        except Exception as e:
            # Redis出错时的降级处理
            logger.error(f"Redis consecutive access limiter error: {e}")
            return True, 0