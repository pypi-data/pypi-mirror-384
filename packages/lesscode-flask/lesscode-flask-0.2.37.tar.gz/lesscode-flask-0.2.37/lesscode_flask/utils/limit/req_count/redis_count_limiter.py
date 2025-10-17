import logging

from flask import request

from lesscode_flask.model.user_limit_policy import UserLimitPolicy
from lesscode_flask.utils.limit.limit_util import limit_key
from lesscode_flask.utils.redis.redis_helper import RedisHelper

logger = logging.getLogger(__name__)

class RedisCountLimiter:
    """Redis限流计数器实现"""
    
    def __init__(self, redis_key):
        self.redis_key = redis_key

    def is_allowed(self, user_limit_policy: UserLimitPolicy):
        """
        检查是否允许请求
        :return: (allowed, remaining)
        """
        count = user_limit_policy.count_limit_count
        time_window = user_limit_policy.count_limit_window_sec
        count_limit_enable = user_limit_policy.count_limit_enable
        limit_white_list = user_limit_policy.white_list
        cost = 1 # 每次消耗一次数
        request_url = request.path
        # 未启用限流 或者 在白名单中 直接返回允许
        if count_limit_enable == 0 or request_url in limit_white_list:
            # 白名单访问 直接返回None
            return True, 0
        #  限流键
        key = f"limit_count:{limit_key(request_url)}"

        try:
            remaining = RedisHelper(self.redis_key).sync_get(key)
            if remaining is None:
                remaining = count-cost
                RedisHelper(self.redis_key).sync_set(key,remaining,time_window)
            else:
                # 键存在，每次减少相应数量
                remaining = RedisHelper(self.redis_key).sync_incrby(name=key,amount=0- cost)
            if remaining < 0:
                return False, remaining
            else:
                return True, remaining
        except Exception as e:
            # Redis出错时的降级处理
            logger.error(f"Redis count limiter error: {e}")
            return True, remaining
