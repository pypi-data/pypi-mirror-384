from lesscode_flask.model.base_model import BaseModel
from lesscode_flask.utils.helpers import generate_uuid
from sqlalchemy import Column, DateTime, JSON, text, String, Integer, Float, DOUBLE


class LcAuthResourceParamTemplate(BaseModel):
    __tablename__ = 'lc_auth_resource_param_template'
    __table_args__ = {'comment': '访问日志'}
    __bind_key__ = 'auth_db'

    id = Column(String(32), primary_key=True, insert_default=generate_uuid)
    param_name = Column(String(32), comment='参数名称')
    param_ch_name = Column(String(64), comment='参数中文名称')
    param_description = Column(String(255), comment='参数描述')
    param_type = Column(Integer, comment='参数类型')
    param_sample = Column(JSON, comment='参数样例')

    create_user_id = Column(String(36), nullable=False, comment='创建人id')
    create_user_name = Column(String(36), nullable=False, comment='创建人用户名')
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), comment='创建时间')
