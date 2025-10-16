import logging
from importlib import import_module

from lesscode_flask.db.executor import QueryExecutor, QueryExecutionError
from lesscode_flask.model.parameterized_query import ParameterizedQuery


def execute_query(
        query_text, parameters,
        query_runner, should_apply_auto_limit=True
):
    """
    执行查询操作
    :param query_text: 待执行语句
    :param parameters: 查询参数数
    :param query_runner: 查询执行器
    :param should_apply_auto_limit:
    :return:
    """
    try:
        query = ParameterizedQuery(query_text)
        if parameters is None:
            parameters = {}
        query.apply(parameters)
        query_text = query.query
        # query_text = query_runner.apply_auto_limit(query.text, should_apply_auto_limit)
        logging.info("query_text:{}".format(query_text))
        return QueryExecutor(
            query_text,
            query_runner
        ).run()
    except Exception as e:
        # models.db.session.rollback()
        raise e


def execute(query_text, parameters, query_runner, should_apply_auto_limit=True):
    """
        执行原生sql操作
        :param query_text: 待执行语句
        :param parameters: 查询参数数
        :param query_runner: 查询执行器
        :param should_apply_auto_limit:
        :return:
        """
    try:
        query = ParameterizedQuery(query_text)
        if parameters is None:
            parameters = {}
        query.apply(parameters)
        query_text = query.query
        # query_text = query_runner.apply_auto_limit(query.text, should_apply_auto_limit)
        logging.info("query_text:{}".format(query_text))
        return QueryExecutor(
            query_text,
            query_runner
        ).exec()
    except Exception as e:
        # models.db.session.rollback()
        raise e


# from flask_sqlalchemy import SQLAlchemy
try:
    flask_sqlalchemy = import_module("flask_sqlalchemy")
except ImportError as e:
    raise Exception(f"flask_sqlalchemy is not exist,run:pip install Flask-SQLAlchemy==3.1.1")


class LessCodeSQLAlchemy(flask_sqlalchemy.SQLAlchemy):
    pass
    # def apply_driver_hacks(self, app, info, options):
    #     options.update(json_serializer=json_dumps)
    #     if settings.SQLALCHEMY_ENABLE_POOL_PRE_PING:
    #         options.update(pool_pre_ping=True)
    #     return super(RedashSQLAlchemy, self).apply_driver_hacks(app, info, options)
    #
    # def apply_pool_defaults(self, app, options):
    #     super(RedashSQLAlchemy, self).apply_pool_defaults(app, options)
    #     if settings.SQLALCHEMY_ENABLE_POOL_PRE_PING:
    #         options["pool_pre_ping"] = True
    #     if settings.SQLALCHEMY_DISABLE_POOL:
    #         options["poolclass"] = NullPool
    #         # Remove options NullPool does not support:
    #         options.pop("max_overflow", None)
    #     return options


# db = LessCodeSQLAlchemy(
#     session_options={"expire_on_commit": False},
#    engine_options={"json_serializer": json_dumps, "json_deserializer": json_loads}, )
db = LessCodeSQLAlchemy()
