# coding: utf-8
import json
from typing import Union


class UserLimitPolicy():

   def __init__(
    self,
    id: str= None,
    policy_name: str= None,
    client_id: str= None,
    rate_limit_enable: int = 0,
    rate_limit_window_sec: int = 10,
    rate_limit_rate: int = 5,
    rate_limit_burst: int = 0,
    count_limit_enable: int = 0,
    count_limit_window_sec: int = 43200,
    count_limit_count: int = 500,
    consecutive_limit_count = 30,  # 连续访问次数限制，默认30次
    consecutive_limit_enable = 0,  # 连续访问限制是否启用，0-不启用，1-启用
    white_list: Union[str, list] = None,
    alert_webhook_url: str = None,
):
    """
    初始化 AuthUserLimitPolicy 对象。

    :param policy_name: 限流策略名称
    :param client_id: 所属应用 ID
    :param rate_limit_enable: 是否启用频率限流（默认 0）
    :param rate_limit_window_sec: 频率窗口时间（秒，默认 1）
    :param rate_limit_rate: 每窗口期内允许请求数（QPS，默认 1）
    :param rate_limit_burst: 允许突发流量数（默认 0）
    :param count_limit_enable: 是否启用计数量限流（默认 0）
    :param count_limit_window_sec: 计数窗口时间（秒，默认 43200）
    :param count_limit_count: 窗口期内最大访问量（默认 500）
    :param white_list: 限流白名单路径列表（JSON 格式）
    :param alert_webhook_url: 报警 webhook URL
    """
    self.id = id
    self.policy_name = policy_name
    self.client_id = client_id
    # 限流参数类型转换为int
    self.rate_limit_enable = int(rate_limit_enable) if rate_limit_enable is not None else 0
    self.rate_limit_window_sec = int(rate_limit_window_sec) if rate_limit_window_sec is not None else 1
    self.rate_limit_rate = int(rate_limit_rate) if rate_limit_rate is not None else 1
    self.rate_limit_burst = int(rate_limit_burst) if rate_limit_burst is not None else 0
    self.count_limit_enable = int(count_limit_enable) if count_limit_enable is not None else 0
    self.count_limit_window_sec = int(count_limit_window_sec) if count_limit_window_sec is not None else 43200
    self.count_limit_count = int(count_limit_count) if count_limit_count is not None else 500
    self.alert_webhook_url = alert_webhook_url
    self.consecutive_limit_count = int(consecutive_limit_count) if consecutive_limit_count is not None else 20  # 连续访问次数限制，默认20次
    self.consecutive_limit_enable = int(consecutive_limit_enable) if consecutive_limit_enable is not None else 0  # 连续访问限制是否启用，0-不启用，1-启用
    # 修改后的 white_list 处理逻辑
    if isinstance(white_list, str):
        self.white_list = json.loads(white_list) if white_list else []
    elif isinstance(white_list, list):
        self.white_list = white_list
    else:
        self.white_list = []

