# -*- coding: utf-8 -*-
import logging
import traceback

from flask import current_app

from lesscode_flask.model.response_result import ResponseResult


class RedisHelper:

    def __init__(self, conn_name):
        try:
            redis_conn_dict = getattr(current_app, "redis_conn_dict")
            redis_conn = redis_conn_dict.get(conn_name)
            if redis_conn:
                self.conn_name = redis_conn
            else:
                ResponseResult.fail(message=f"命名为{conn_name}的redis连接信息不存在")
        except AttributeError:
            logging.error(traceback.print_stack())
            ResponseResult.fail(message=f"未配置名为{conn_name}的redis 连接信息")

    def get_connection(self):
        return self.conn_name

    def sync_set(self, name, value, ex=None, px=None, nx: bool = False, xx: bool = False, keepttl: bool = False):
        return self.get_connection().set(name, value, ex, px, nx, xx, keepttl)

    def sync_get(self, name):
        return self.get_connection().get(name)

    def sync_incrby(self, name,amount):
        return self.get_connection().incrby(name,amount)

    def sync_keys(self, pattern):
        return self.get_connection().keys(pattern=pattern)

    def sync_exists(self, *name):
        return self.get_connection().exists(*name)

    def sync_delete(self, names):
        if isinstance(names, list) or isinstance(names, tuple):
            return self.get_connection().delete(*names)
        else:
            return self.get_connection().delete(names)

    def sync_rpush(self, name, values: list, time=None):
        con = self.get_connection()
        res = con.rpush(name, *values)
        if time:
            con.expire(name, time)
        return res

    def sync_hset(self, name, key=None, value=None, mapping=None, time=None):
        con = self.get_connection()
        res = con.hset(name, key=key, value=value, mapping=mapping)
        if time:
            con.expire(name, time)
        return res

    def sync_hgetall(self, name):
        return self.get_connection().hgetall(name)

    def sync_hget(self, name, key):
        return self.get_connection().hget(name, key)

    def sync_hdel(self, name, key):
        return self.get_connection().hdel(name, key)

    def sync_hexists(self, name, key):
        return self.get_connection().hexists(name, key)

    def sync_hincrby(self, name, key, amount: int):
        return self.get_connection().hincrby(name, key, amount)

    def sync_hincrbyfloat(self, name, key, amount: float):
        return self.get_connection().hincrbyfloat(name, key, amount)

    def sync_hkeys(self, name):
        return self.get_connection().hkeys(name)

    def sync_hlen(self, name):
        return self.get_connection().hlen(name)

    def sync_hmset(self, name, mapping, time=None):
        con = self.get_connection()
        res = con.hmset(name, mapping)
        if time:
            con.expire(name, time)
        return res

    def sync_hmget(self, name, keys, *args):
        return self.get_connection().hmget(name, keys, *args)

    def sync_hsetnx(self, name, key, value):
        return self.get_connection().hsetnx(name, key, value)

    def sync_hvals(self, name):
        return self.get_connection().hvals(name)

    def sync_sadd(self, name, values: list, time=None):
        con = self.get_connection()
        res = con.sadd(name, *values)
        if time:
            con.expire(name, time)
        return res

    def sync_scard(self, name):
        return self.get_connection().scard(name)

    def sync_sismember(self, name, value):
        return self.get_connection().sismember(name, value)

    def sync_smembers(self, name):
        return self.get_connection().smembers(name)

    def sync_spop(self, name, count):
        return self.get_connection().spop(name, count)

    def sync_srem(self, name, *values):
        return self.get_connection().srem(name, *values)
