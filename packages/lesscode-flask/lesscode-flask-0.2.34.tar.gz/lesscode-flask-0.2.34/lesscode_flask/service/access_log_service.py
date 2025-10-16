
from lesscode_flask.model.access_log import AccessLog
from lesscode_flask.service.base_service import BaseService


class AccessLogService(BaseService):
    def __init__(self):
        super().__init__(AccessLog)
