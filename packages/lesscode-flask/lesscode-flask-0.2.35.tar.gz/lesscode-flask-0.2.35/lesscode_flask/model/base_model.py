import json
import logging
from datetime import datetime
from typing import Optional, Type, Any

from sqlalchemy.sql.type_api import _T

from lesscode_flask.db import db


class BaseModel(db.Model):
    __abstract__ = True
    __bind_key__ = 'default'

    # def to_dict(self):
    #     return {c.name: getattr(self, c.name) for c in self.__table__.columns}


from sqlalchemy import TypeDecorator, VARCHAR, Dialect


class JSONEncodedDict(TypeDecorator):
    """数据字段存储为json格式字符串 ，进行互转"""

    def process_literal_param(self, value: Optional[_T], dialect: Dialect) -> str:
        pass

    impl = VARCHAR
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value is not None and not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

    # impl = Text
    # cache_ok = True  # 添加此属性
    #
    # def process_bind_param(self, value, dialect):
    #     if value is not None:
    #         value = json.dumps(value)
    #     return value
    #
    # def process_result_value(self, value, dialect):
    #     if value is not None:
    #         value = json.loads(value)
    #     return value

class DatetimeEncodedString(TypeDecorator):
    """数据字段日期与字符串进行互转"""

    @property
    def python_type(self) -> Type[Any]:
        return str

    def process_literal_param(self, value: Optional[_T], dialect: Dialect) -> str:
        return value

    impl = VARCHAR
    cache_ok = True

    def __init__(self, date_format="%Y-%m-%d %H:%M:%S"):
        self.date_format = date_format
        super().__init__()

    # date_format = "%Y-%m-%d %H:%M:%S"
    def process_bind_param(self, value, dialect):
        # 将实体属性转化为数据库值
        if value is not None:
            value = datetime.strptime(value, self.date_format)
        return value

    def process_result_value(self, value, dialect):
        # 数据库值转化为实体属性。
        if value is not None:
            value = value.strftime(self.date_format)
        return value
