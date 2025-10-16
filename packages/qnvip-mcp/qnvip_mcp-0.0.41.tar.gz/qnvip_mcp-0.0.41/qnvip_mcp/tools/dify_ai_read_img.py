# util/qnvip_tools.py
import os
from typing import Annotated,List
from fastmcp import Context
import requests



async def ai_read_img(
    img_urls: Annotated[List[str], '待读取的图片的链接,List[str]格式'],
    reading_requirements: Annotated[str, '读取要求'],
    action: Annotated[int, '1仅识别图片内容 2对需求点逐个携带测试用例要求再次去识别相关的图片生成测试用例，数字类型 必填'],
    enums: Annotated[str, '当action=2时传入图中的枚举字典,action=1时不必填'],
    ctx: Context,
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
        "inputs": {
            "action":action,
            "enums":enums
        },
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