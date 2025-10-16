from lesscode_flask.model.resource_param_template import LcAuthResourceParamTemplate
from lesscode_flask.service.base_service import BaseService


class ResourceParamTemplateService(BaseService):
    def __init__(self):
        super().__init__(LcAuthResourceParamTemplate)
