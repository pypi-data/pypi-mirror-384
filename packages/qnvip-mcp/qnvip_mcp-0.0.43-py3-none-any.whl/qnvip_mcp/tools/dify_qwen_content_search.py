# util/qnvip_tools.py
import os
from typing import Annotated
import requests


async def search_content(
    query: Annotated[str, '查询内容'],
) -> str:
    """
     搜索查询公司文档，代码规范，技术文档，需求文档，周报，日报，代码
     """
    token = os.environ.get('PERSONAL_AUTHORIZATION')
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
