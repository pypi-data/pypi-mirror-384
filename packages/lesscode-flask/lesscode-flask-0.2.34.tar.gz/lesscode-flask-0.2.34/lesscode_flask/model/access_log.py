from lesscode_flask.model.base_model import BaseModel, DatetimeEncodedString, JSONEncodedDict
from lesscode_flask.utils.helpers import generate_uuid
from sqlalchemy import Column, JSON, text, String, Integer, DOUBLE, DateTime


class AccessLog(BaseModel):
    __tablename__ = 'lc_access_log'
    __table_args__ = {'comment': '访问日志'}
    __bind_key__ = 'log_db'

    id = Column(String(32), primary_key=True, insert_default=generate_uuid)
    request_id = Column(String(32), comment='请求id')
    display_name = Column(String(64), comment='显示名')
    obj_id = Column(String(255), comment='对象标识，用户id或者应用id')
    type = Column(Integer, comment='请求类型0:用户请求，1:API用户，2:匿名用户')
    sub = Column(String(32), comment='jwt登录的应用id')
    client_id = Column(String(32), comment='资源所属应用id')
    resource_id = Column(String(32), comment='资源id')
    resource_label = Column(String(128), comment='菜单显示名(操作)')
    url = Column(String(255), comment='访问地址')
    referrer = Column(String(255), comment='访问来源')
    client_ip = Column(String(255), comment='客户端ip')
    location = Column(String(255), comment='IP地区')
    user_agent = Column(String(512), comment='客户端')
    params = Column(JSONEncodedDict)
    start_time = Column(DOUBLE, comment='开始时间')
    end_time = Column(DOUBLE, comment='结束时间')
    duration = Column(DOUBLE, comment='耗时')
    status_code = Column(Integer, comment='响应状态码')
    create_user_id = Column(String(36), nullable=False, comment='创建人id')
    create_user_name = Column(String(36), nullable=False, comment='创建人用户名')
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), comment='创建时间')
