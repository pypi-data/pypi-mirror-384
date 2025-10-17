import functools
import logging
import re


def param_verification(func):
    """
    装饰器函数，用于检测函数参数中是否包含 SQL 注入风险。

    :param func: 被装饰的原始函数
    :return: 包装后的函数，会在执行前进行 SQL 注入检测
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 检查关键字参数中是否包含 SQL 注入风险
        if contains_sql_injection(kwargs):
            raise Exception("SQL 注入 detected")

        return func(*args, **kwargs)

    return wrapper


def is_sql_injection(value):
    """
    检测字符串是否包含常见的 SQL 注入特征。

    :param value: 待检测的字符串
    :return: 如果包含 SQL 注入特征则返回 True，否则返回 False
    """
    if not isinstance(value, str):
        return False  # 只检查字符串类型的数据

    # 常见 SQL 注入特征
    sql_patterns = [
        r"(?i)(\bAND\b|\bOR\b)[\s(]*\d+[\s)]*=[\s(]*\d+[\s)]*",  # 逻辑表达式
        r"(?i)\b(select|union|insert|update|delete|drop|alter|create|truncate|exec|execute|sleep)\b",  # 关键 SQL 语句
        r"(?i)( or | and )\d+=\d+",  # 布尔盲注
        r"(?i)(char|concat|case when)\s*\(",  # SQL 函数
        r"(--|;)",  # 注释符号或语句结束符
        r"(?i)'[\s\d]*or[\s\d]*'",  # 典型 SQL 盲注
    ]

    for pattern in sql_patterns:
        if re.search(pattern, value):
            return True  # 发现 SQL 注入特征

    return False


def contains_sql_injection(data):
    """
    递归检测数据结构中是否包含 SQL 注入风险。

    支持的数据类型包括：字符串、列表、元组和字典。
    对于其他类型（如 int、float、None）将直接返回 False。

    :param data: 待检测的数据，可以是任意嵌套结构
    :return: 如果发现 SQL 注入风险则返回 True，否则返回 False
    """
    if isinstance(data, str):  # 单个字符串
        return is_sql_injection(data)

    if isinstance(data, list):  # 列表中的每个元素
        return any(contains_sql_injection(item) for item in data)
    if isinstance(data, tuple):  # 元组中的每个元素
        return any(contains_sql_injection(item) for item in data)

    if isinstance(data, dict):  # 递归检查字典中的值
        return any(contains_sql_injection(value) for value in data.values())

    return False  # 其他类型（int, float, None）不检测

