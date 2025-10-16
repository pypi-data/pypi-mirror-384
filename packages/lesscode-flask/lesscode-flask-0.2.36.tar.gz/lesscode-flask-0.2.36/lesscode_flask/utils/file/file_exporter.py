import importlib
import os
import uuid
from urllib.parse import quote

from flask import send_file

from lesscode_flask.setting import BaseConfig
from lesscode_flask.utils.helpers import app_config
from lesscode_flask.utils.oss.ks3_oss import Ks3Oss


def judge_file_name(parent_path, file_name, extension, index=1):
    while os.path.isfile(f'{parent_path}/{file_name}.{extension}'):
        if index > 1:
            file_name = file_name.replace(f'({index - 1})', f'({index})')
        else:
            file_name = f'{file_name}({index})'

        index = index + 1
    return f'{parent_path}/{file_name}.{extension}', f'{file_name}.{extension}'


def format_to_table_download(table_head_list=None, table_body_list=None):
    data_index_list = [one['dataIndex'] for one in table_head_list]
    table_head_map_dict = {one['dataIndex']: one['title'] for one in table_head_list}
    sta_map_dict = {}
    for one in table_body_list:
        for tag in data_index_list:
            if tag not in sta_map_dict:
                sta_map_dict[tag] = [one[tag]]
            else:
                sta_map_dict[tag].append(one[tag])
    sta_map_dict = {table_head_map_dict[k]: v for k, v in sta_map_dict.items()}
    return sta_map_dict


def export(table_head_list=None, table_body_list=None, file_name=None, extension="xlsx", export_path=None,
           is_upload_ks3=False, bucket_name=None):
    """
    :param is_upload_ks3: 是否上传至ks3
    :param table_head_list: [
            {
                "title": "企业名称",
                "dataIndex": "name"
            },
            {
                "title": "省",
                "dataIndex": "reg_province"
            }
        ]
    :param table_body_list: [
            {
                 "name":"丽丽"
                 "reg_province":"北京市"
            }

    ]
    :param file_name:导出文件的名称
    :param extension:扩展名
    :param export_path: 导出目录 默认是静态目录下的download
    :return:
    """
    data = format_to_table_download(table_head_list, table_body_list)
    try:
        pandas = importlib.import_module("pandas")
    except ImportError:
        raise Exception(f"pandas is not exist,run:pip install pandas==2.2.2")

    df = pandas.DataFrame(data=data)
    # 定义下载目录，如果没有就新建
    if not export_path:
        export_path = f'{BaseConfig.STATIC_PATH}/download'
    if not os.path.exists(export_path):
        os.mkdir(export_path)
    # 判断文件的名称如果存在则加(n)
    file_path, file_name = judge_file_name(export_path, file_name, extension)

    df.to_excel(file_path, index=False)

    file_name = quote(file_name)

    if is_upload_ks3:
        ks = Ks3Oss()
        if not bucket_name:
            bucket_name = app_config.get("KS3_CONNECT_CONFIG", {}).get("bucket_name")
        response = ks.save(key=file_name, bucket_name=bucket_name, policy="public-read", filename=file_path,
                           content_type="filename")
    else:
        response = send_file(
            file_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=False,
            download_name=file_name
        )
    # 下载完成删除文件
    os.remove(file_path)
    return response
