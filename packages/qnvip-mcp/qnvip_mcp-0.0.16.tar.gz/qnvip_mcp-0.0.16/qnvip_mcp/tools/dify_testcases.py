# util/qnvip_tools.py
from dotenv import load_dotenv

load_dotenv("conf/.env")
import os
from typing import Annotated,List

import requests
from fastmcp import Context


async def testcases_instructions(
    file_name: Annotated[str, '需要生成测试用例的需求文档名字'],
    has_img: Annotated[int, '是否包含图片1是0否，数字类型'],
    ctx: Context
) -> str:
    """
     生成测试用例的todolist,生成测试用例的工作流程和规范
     """
    token = ctx.request_context.request.headers.get('personal-authorization')
    headers = {
        "Authorization": f"Bearer {os.environ.get('DIFY_GEN_TESTCASES_BY_TXT_API_KEY')}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": {
            "file_name": file_name,
            "has_img": has_img,
         },
        "query": file_name,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": token
    }

    DIFY_API_URL = os.environ.get('DIFY_API_URL')
    response = requests.post(f"{DIFY_API_URL}/chat-messages", headers=headers, json=payload, timeout=None)
    response.raise_for_status()

    response_data = response.json()
    return response_data.get("answer", "响应数据为空")

