import logging

import json

import requests

logger = logging.getLogger(__name__)

def fs_webhook(webhook_url:str,title:str, fs_content:list):
    """
    发送飞书 webhook 消息

    参数:
        webhook_url (str): 飞书 webhook 的 URL 地址
        title (str): 消息的标题
        fs_content (str or list): 消息内容，可以是字符串或字符串列表

    返回值:
        无返回值，直接发送 HTTP 请求
    """
    headers = {'Content-Type': 'application/json;charset=utf-8'}

    # # 根据内容类型构建飞书消息格式
    # if isinstance(content, list):
    #     fs_content = []
    #     for i in content:
    #         fs_content.append({
    #             "tag": "text",
    #             "text": f"{i}\n"
    #         })
    # else:
    #     fs_content = [{
    #         "tag": "text",
    #         "text": f"{content}\n"
    #     }]

    # 构造飞书消息的 JSON 结构
    json_text = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [
                        fs_content
                    ]
                }
            }
        }
    }

    # 发送 POST 请求并记录响应结果
    result = requests.post(webhook_url, json.dumps(json_text), headers=headers).content
    logger.info(result)

