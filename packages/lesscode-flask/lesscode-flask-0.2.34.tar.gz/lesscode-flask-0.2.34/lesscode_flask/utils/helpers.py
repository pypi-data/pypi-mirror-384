import logging

import iputil
from phone import Phone


class app_config:
    app = None

    @staticmethod
    def config(app):
        app_config.app = app

    @staticmethod
    def get(key, default=None):
        """
        获取配置
        :param key: 配置key
        :param default: 默认值
        :return:
        """
        # from flask import current_app
        # return current_app.config.get(key, default)
        return app_config.app.config.get(key, default)


def result_to_dict(result):
    """
    将结果对象或SQLAlchemy查询结果转换为字典
    :param result:
    :return:
    """
    if isinstance(result, list):
        return [result_to_dict(r) for r in result]

    if hasattr(result, "_fields"):
        key_list = list(result._fields)
        return dict(zip(key_list, result))

    if hasattr(result, "__dict__"):
        return {k: v for k, v in result.__dict__.items() if not k.startswith('_')}
    return result


def build_tree(data, parent: str = "parent_id", pk: str = "id"):
    """
    构建树形结构数据。
    根据给定的数据列表和父节点标识，将平面数据结构转换为树形结构。

    参数:
    - data: 平面数据列表，每个元素包含一个节点及其父节点ID。
    - parent: 父级字段名字符串，默认为"parent_id"，用于查找父节点。
    - pk: 主键字段名字符串，默认为"id"，用于标识父节点。

    返回:
    - tree: 转换后的树形结构数据列表。
    """
    # 创建一个字典来快速查找节点
    node_map = {}
    _sort_key = 0
    # 为数据增加一个_sort_key属性用于排序
    for item in data:
        item['_sort_key'] = _sort_key
        node_map[item[pk]] = item
        _sort_key += 1
    # 初始化根节点列表
    tree_data = []

    for item in data:
        parent_id = item[parent]
        if parent_id in node_map:
            # 如果存在父节点，则将当前节点添加为父节点的子节点
            parent_node = node_map[parent_id]
            if 'children' not in parent_node:
                parent_node['children'] = []
            parent_node['children'].append(item)
        else:
            # 如果没有父节点，则当前节点为根节点
            tree_data.append(item)

    def sort_tree(data):
        data.sort(key=lambda x: x['_sort_key'])
        for child in data:
            if 'children' in child:
                sort_tree(child['children'])

    sort_tree(tree_data)
    return tree_data


def generate_uuid():
    """
    生成UUID
    :return:
    """
    import uuid
    return uuid.uuid4().hex.replace("-", "")


# def get_start_port():
#     """
#     获取启动端口
#     :return:
#     """
#     import sys
#     arg_list = sys.argv
#     for a in arg_list:
#         if "--port" in a:
#             return a.split("=")[1]
#     return "5000"


def parameter_validation(obj: dict):
    """
    验证参数对象中非None的键值
    :return:
    """
    return {k: v for k, v in obj.items() if v is not None}


def parse_boolean(s):
    """
    将字符串转换为布尔值。
    :param s: 待转换的字符串
    :return:
    """
    s = str(s)
    s = s.strip().lower()
    if s in ("yes", "true", "on", "1"):
        return True
    # elif s in ("no", "false", "off", "0", "none"):
    #     return False
    else:
        # 其余不在判断全返False
        return False


def inject_args(req, func, view_args={}):
    import inspect

    """
    实现参数自动注入
    :param req: 请求对象
    :param func: 请求处理函数
    :param view_args: 路径上获取的参数
    :return:
    """
    jsons = {}
    args = req.args
    form = req.form
    files = req.files
    if req.mimetype == 'application/json':
        try:
            if req.json is not None:
                jsons = req.json
        except Exception as e:
            pass
    # 合并args、form和json参数字典
    arguments = dict(**args, **form, **jsons, **files, **view_args)
    # 获取处理方法的 参数签名
    parameters = inspect.signature(func).parameters.items()
    # 获取所有参数名称
    parameter_names = [parameter_name for parameter_name, parameter in parameters]
    kwargs = {}
    # 检查传入的参数中 哪些不在参数列表中，单独存储
    for key in arguments.keys():
        if key not in parameter_names:
            kwargs[key] = arguments[key]
    params_dict = {}
    # parameterName 参数名称, parameter 参数对象
    for parameter_name, parameter in parameters:
        # 依据参数名称，获取请求参数值
        argument_value = arguments.get(parameter_name)
        # 兼容**kwargs 参数
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            argument_value = kwargs
        if argument_value is not None:
            # 获取形参类型
            parameter_type = parameter.annotation
            # 形参类型为空，尝试获取形参默认值类型
            if parameter_type is inspect.Parameter.empty:
                parameter_type = type(parameter.default)
            if parameter_type == int:
                params_dict[parameter_name] = int(argument_value)
            elif parameter_type == float:
                params_dict[parameter_name] = float(argument_value)
            elif parameter_type == bool:
                params_dict[parameter_name] = parse_boolean(argument_value)
            else:
                # 其余都按str处理
                params_dict[parameter_name] = argument_value
    return params_dict


def mustache_render(template, **kwargs):
    """
    模板参数渲染
    :param template: 模板
    :param kwargs:参数
    :return:
    """
    from jinja2 import Template
    # 创建模板对象
    template = Template(template)
    # 渲染模板
    return template.render(**kwargs)


def format_list_index(data_list, index=1, index_key="index"):
    """
    为数据源提供
    :param data_list:
    :param index:
    :param index_key:
    :return:
    """
    for data in data_list:
        data[index_key] = str(index)
        index = index + 1


def format_page_index(data_list, page_num, page_size, index_key="index"):
    """

    :param data_list:
    :param page_num:
    :param page_size:
    :param index_key:
    :return:
    """
    index = (page_num - 1) * page_size + 1
    format_list_index(data_list, index, index_key=index_key)


def get_phone_location(phone: str):
    try:
        phone_info = Phone().find(phone)
        return phone_info
    except Exception as e:
        return None


def get_ip_location(ip):
    region: str = iputil.get_region(ip)
    data = {
        "country": "",
        "area": "",
        "province": "",
        "city": "",
        "isp": ""
    }
    region_info_list = region.split("|")
    if len(region_info_list):
        data = {
            "country": region_info_list[0],
            "province": region_info_list[2],
            "city": region_info_list[3],
            "isp": region_info_list[4]
        }
    return data
