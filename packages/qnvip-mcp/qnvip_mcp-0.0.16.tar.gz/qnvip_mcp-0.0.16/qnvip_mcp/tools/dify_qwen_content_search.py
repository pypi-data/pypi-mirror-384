# util/qnvip_tools.py
from dotenv import load_dotenv

load_dotenv("conf/.env")
import os
from typing import Annotated,List

import requests
from fastmcp import Context


async def content(
    query: Annotated[str, '查询内容'],
    ctx: Context
) -> str:
    """
     搜索查询公司文档，代码规范，技术文档，需求文档，周报，日报，代码
     """
    token = ctx.request_context.request.headers.get('personal-authorization')
    headers = {
        "Authorization": f"Bearer {os.environ.get('DIFY_GEN_BY_TXT_API_KEY')}",
        "Content-Type": "application/json",
        "PersonalAuthorization": token,  # 来自客户端配置
    }

    payload = {
        "inputs": {"personal_token": token},
        "query": query,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": token
    }

    DIFY_API_URL = os.environ.get('DIFY_API_URL')
    response = requests.post(f"{DIFY_API_URL}/chat-messages", headers=headers, json=payload, timeout=None)
    response.raise_for_status()

    response_data = response.json()
    return response_data.get("answer", "响应数据为空")


async def generate_test_cases_from_images(
    query: Annotated[str, '查询内容'],
    image_urls: Annotated[List[str], '本地图片的绝对路径'],
    ctx: Context
) -> str:
    """
      搜索查询公司文档，代码规范，技术文档，需求文档，周报，日报，代码
      """
    token = ctx.request_context.request.headers.get('personal-authorization')
    headers = {
        "Authorization": f"Bearer {os.environ.get('DIFY_GEN_BY_IMG_API_KEY')}",
        "Content-Type": "application/json",
        "PersonalAuthorization": token,  # 来自客户端配置
    }

    wrap_image_urls = [
        {
            "type": "image",
            "transfer_method": "remote_url",
            "url": image_url
        }
        for image_url in image_urls
    ]
    payload = {
        "inputs": {"personal_token": token},
        "query": query,
        "image_urls": wrap_image_urls,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": token
    }

    DIFY_API_URL = os.environ.get('DIFY_API_URL')
    response = requests.post(f"{DIFY_API_URL}/chat-messages", headers=headers, json=payload, timeout=None)
    response.raise_for_status()

    response_data = response.json()
    return response_data.get("answer", "响应数据为空")

async def gen_testcases(
    query: Annotated[str, '搜索查询内容'],
    ctx: Context,
    # image_urls: Annotated[List[str], '本地图片的绝对路径,数组，可为空']
) -> str:
    """
      搜索查询公司文档，代码规范，技术文档，需求文档，周报，日报，代码
      """
    return await content(query, ctx)
    # if not query and not image_urls:
    #     return "query 和 image_urls 不能同时为空"
    #
    # if not image_urls:
    #     return await content(query,ctx)
    # else :
    #     return await generate_test_cases_from_images(query,image_urls,ctx)