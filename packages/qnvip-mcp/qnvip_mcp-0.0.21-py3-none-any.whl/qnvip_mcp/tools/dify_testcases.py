# util/qnvip_tools.py
from dotenv import load_dotenv

load_dotenv("conf/.env")
import os
from typing import Annotated

import requests



async def testcases_instructions(
    article_name: Annotated[str, '需要生成测试用例的需求文档名字 可为空'],
    has_img: Annotated[int, '是否包含图片1是0否，数字类型 必填'],
) -> str:
    """
     生成测试用例的todolist,生成测试用例的工作流程和规范
     """
    DIFY_GEN_TESTCASES_BY_TXT_API_KEY = os.environ.get('DIFY_GEN_TESTCASES_BY_TXT_API_KEY')

    headers = {
        "Authorization": f"Bearer {DIFY_GEN_TESTCASES_BY_TXT_API_KEY}",
        "Content-Type": "application/json",
    }
    print(f"Bearer ---------- {DIFY_GEN_TESTCASES_BY_TXT_API_KEY}")

    payload = {
        "inputs": {
            "article_name": article_name,
            "has_img": has_img,
         },
        "query": "none",
        "response_mode": "blocking",
        "conversation_id": "",
        "user": "none"
    }

    DIFY_API_URL = os.environ.get('DIFY_API_URL')
    response = requests.post(f"{DIFY_API_URL}/chat-messages", headers=headers, json=payload, timeout=None)
    response.raise_for_status()

    response_data = response.json()
    return response_data.get("answer", "响应数据为空")

