# util/qnvip_tools.py
from dotenv import load_dotenv

load_dotenv("conf/.env")
import os
from typing import Annotated,List

import requests



async def ai_read_img(
    img_urls: Annotated[List[str], '待读取的图片的链接,List[str]格式'],
    reading_requirements: Annotated[str, '读取要求,str'],
) -> str:

    DIFY_READ_IMG_API_KEY = os.environ.get('DIFY_READ_IMG_API_KEY')

    headers = {
        "Authorization": f"Bearer {DIFY_READ_IMG_API_KEY}",
        "Content-Type": "application/json",
    }

    form_img_urls = [
        {
            "type": "image",
            "transfer_method": "remote_url",
            "url": image_url
        }
        for image_url in img_urls
    ]
    payload = {
        "inputs": {},
        "query": reading_requirements,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": "none",
        "files":form_img_urls
    }

    DIFY_API_URL = os.environ.get('DIFY_API_URL')
    response = requests.post(f"{DIFY_API_URL}/chat-messages", headers=headers, json=payload, timeout=None)
    response.raise_for_status()

    response_data = response.json()
    return response_data.get("answer", "响应数据为空")

