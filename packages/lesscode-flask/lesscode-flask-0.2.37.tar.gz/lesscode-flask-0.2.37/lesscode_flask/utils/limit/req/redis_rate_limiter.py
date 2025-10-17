import time
import logging

from flask import request

from lesscode_flask.model.user_limit_policy import UserLimitPolicy
from lesscode_flask.utils.limit.limit_util import limit_key
from lesscode_flask.utils.redis.redis_helper import RedisHelper

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Redis限流实现
    """

    def __init__(self, redis_key):
        self.redis_key = redis_key

    def is_limited(self,user_limit_policy: UserLimitPolicy) -> tuple:
        """
        检查是否触发限流
        :param user_limit_policy: 策略信息
        :return: (allowed,delay, excess) 是否触发限流 延迟时间和超出数量
        """

        rate: float = user_limit_policy.rate_limit_rate
        burst: float = user_limit_policy.rate_limit_burst
        time_window: int = user_limit_policy.rate_limit_window_sec
        rate_limit_enable = user_limit_policy.rate_limit_enable
        limit_white_list = user_limit_policy.white_list
        request_url = request.path
        # 未启用限流 或者 在白名单中 直接返回允许
        if rate_limit_enable == 0 or  request_url in limit_white_list:
            # 白名单访问 直接返回None
            return True, 0, 0
        # 构造Redis键
        key = f"limit_req:{limit_key(request_url)}"
        # 存储键的键
        excess_key = f"{key}excess"
        # 存储最近一次请求时间毫秒的键
        last_key = f"{key}last"
        # 当前时间的毫秒表示形式
        now = time.time() * 1000  # 转换为毫秒

        try:
            # 获取上次记录的信息
            excess = RedisHelper(self.redis_key).sync_get(excess_key)
            last =RedisHelper(self.redis_key).sync_get(last_key)

            if excess is not None and last is not None:
                excess = float(excess)
                # 获取最近一次请求的时间毫秒值
                last = float(last)
                # 计算当前与最近一次访问的时间差
                elapsed = now - last
                # 根据时间差计算当前的excess值
                excess = max(excess - (rate * abs(elapsed) / 1000*time_window) + 1, 0)
            else:
                excess = 0
            # 返回延迟时间和超出数量
            delay = excess / rate
            # 检查是否超出限制
            if excess > burst+rate:
                return False, delay, excess # 被拒绝
            # 更新Redis中的值
            RedisHelper(self.redis_key).sync_set(excess_key, excess)
            RedisHelper(self.redis_key).sync_set(last_key, now)
            return True,delay, excess

        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}")
            return True, 0,0
        # if not key: # 没有key表示不验证
        #     return True, 0,0
        # # 构造Redis键
        # key = f"limit_req:{key}"
        # # 存储键的键
        # excess_key = f"{key}excess"
        # # 存储最近一次请求时间毫秒的键
        # last_key = f"{key}last"
        # # 当前时间的毫秒表示形式
        # now = time.time() * 1000  # 转换为毫秒
        #
        # try:
        #     # 获取上次记录的信息
        #     excess = RedisHelper(self.redis_key).sync_get(excess_key)
        #     last =RedisHelper(self.redis_key).sync_get(last_key)
        #
        #     if excess is not None and last is not None:
        #         excess = float(excess)
        #         # 获取最近一次请求的时间毫秒值
        #         last = float(last)
        #         # 计算当前与最近一次访问的时间差
        #         elapsed = now - last
        #         # 根据时间差计算当前的excess值
        #         excess = max(excess - (rate * abs(elapsed) / 1000*time_window) + 1, 0)
        #     else:
        #         excess = 0
        #     # 返回延迟时间和超出数量
        #     delay = excess / rate
        #     # 检查是否超出限制
        #     if excess > burst+rate:
        #         return False, delay, excess # 被拒绝
        #     # 更新Redis中的值
        #     RedisHelper(self.redis_key).sync_set(excess_key, excess)
        #     RedisHelper(self.redis_key).sync_set(last_key, now)
        #     return True,delay, excess
        #
        # except Exception as e:
        #     logger.error(f"Redis rate limiter error: {e}")
        #     return True, 0,0
