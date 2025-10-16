from string import Template

from lesscode_flask.service.resource_param_template_service import ResourceParamTemplateService


def get_response_template():
    return {
        "200": {
            "description": "Successful operation",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        },
        "400": {
            "description": "Invalid input data"
        }
    }


def get_request_body(body, required, request_type):
    return {
        "required": True,
        "content": {
            request_type: {
                "schema": {
                    "type": "object",
                    "properties": body,
                    "required": required
                }
            }
        }
    }


def get_header_template():
    return [
        {
            "name": "App-Key",
            "in": "header",
            "required": False,
            "schema": {
                "type": "string",
                "description": "App-Key"
            }
        }, {
            "name": "Data-Source-Id",
            "in": "header",
            "required": False,
            "schema": {
                "type": "string",
                "description": "Data-Source-Id"
            }
        }
    ]


def split_doc(rule, app):
    endpoint = rule.endpoint
    view_func = app.view_functions[endpoint]
    doc = view_func.__doc__  # 获取视图函数的 docstring
    inter_desc = ""
    param_desc_dict = {}
    return_desc = ""

    if doc:
        doc_lines = doc.splitlines()  # 将 docstring 拆分成多行
        doc_lines = [d.strip() for d in doc_lines]
        doc_lines = list(filter(lambda x: x, doc_lines))
        inter_desc, param_desc_dict, return_desc = split_annotation_list(doc_lines)
    return inter_desc, param_desc_dict, return_desc


def get_param_template():
    template_list = ResourceParamTemplateService().get_items()
    template_dict = {t["param_name"]: t for t in template_list}
    return template_dict


def split_annotation_list(doc_lines):
    inter_desc = ""
    return_desc = ""
    param_desc_dict = {}
    if len(doc_lines) > 0 and not doc_lines[0].startswith("params") and not doc_lines[0].startswith("return"):
        inter_desc = ""
        for doc in doc_lines:
            if not doc.startswith(":param") and not doc.startswith(":return") and not doc.startswith(
                    "@param") and not doc.startswith("@return"):
                inter_desc += doc
            else:
                break
    if len(doc_lines) > 0 and doc_lines[-1].startswith(":return"):
        return_desc = doc_lines.pop(-1)
    for param in doc_lines:
        try:
            param = param.replace(":param ", "")
            fir_index = param.find(':')
            param_desc_dict[param[:fir_index]] = param[fir_index + 1:]
        except:
            pass
    return inter_desc, param_desc_dict, return_desc
