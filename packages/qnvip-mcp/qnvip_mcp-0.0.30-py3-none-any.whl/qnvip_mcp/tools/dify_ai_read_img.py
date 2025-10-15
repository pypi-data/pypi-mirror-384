# util/qnvip_tools.py
import os
from typing import Annotated,List
from fastmcp import Context
import requests



async def ai_read_img(
    img_urls: Annotated[List[str], '待读取的图片的链接,List[str]格式'],
    reading_requirements: Annotated[str, '读取要求'],
    ctx: Context,
) -> str:
    await ctx.warning(f"----- reading_requirements {reading_requirements}")
    DIFY_READ_IMG_API_KEY = os.environ.get('DIFY_READ_IMG_API_KEY')
    await ctx.warning(f"----- DIFY_READ_IMG_API_KEY {DIFY_READ_IMG_API_KEY}")
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
    await ctx.warning(f"----- DIFY_API_URL {DIFY_API_URL}")
    response = requests.post(f"{DIFY_API_URL}/chat-messages", headers=headers, json=payload, timeout=None)
    response.raise_for_status()

    response_data = response.json()
    return response_data.get("answer", "响应数据为空")


async def main():
    """测试 ai_read_img 方法"""
    # 测试图片URL列表
    test_img_urls = [
        "https://upload-test.qnvipmall.com/tmp/4f88c581-7116-49aa-8203-f065233cda89/222.png",
        "https://upload-test.qnvipmall.com/tmp/4f88c581-7116-49aa-8203-f065233cda89/222.png",
    ]
    
    # 读取要求
    test_reading_requirements = "请描述图片中的内容"
    
    try:
        result = await ai_read_img(test_img_urls, test_reading_requirements)
        print(f"AI读取结果: {result}")
    except Exception as e:
        print(f"测试失败: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())