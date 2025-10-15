import os
import requests
import uuid
from typing import Dict, Any,Annotated,List



def upload_file(file_path: str, system_code: str = "47") -> str:
    """
    上传本地文件到服务器
    
    Args:
        file_path: 本地文件的绝对路径
        system_code: 系统代码，默认为47
        
    Returns:
        str: 上传成功后的完整文件URL
        
    Raises:
        FileNotFoundError: 文件不存在
        requests.RequestException: 上传请求失败
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 从环境变量获取上传URL
    upload_url = os.getenv("FILE_UPLOAD_URL")
    if not upload_url:
        raise ValueError("环境变量UPLOAD_URL未设置")
    
    # 生成唯一的文件key
    file_name = os.path.basename(file_path)
    unique_id = str(uuid.uuid4())
    file_key = f"tmp/{unique_id}/{file_name}"
    
    # 准备上传数据
    files = {
        'file': open(file_path, 'rb')
    }
    
    data = {
        'systemCode': system_code,
        'fileKey': file_key
    }
    
    try:
        # 发送上传请求
        response = requests.post(upload_url, files=files, data=data)
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        if result.get('success') and result.get('code') == 0:
            data_info = result.get('data', {})
            domain = data_info.get('domain', '')
            file_key_response = data_info.get('fileKey', '')
            
            # 返回完整的文件URL
            full_url = f"{domain.rstrip('/')}/{file_key_response}"
            return full_url
        else:
            raise requests.RequestException(f"上传失败: {result.get('message', '未知错误')}")
            
    except requests.RequestException as e:
        raise requests.RequestException(f"上传请求失败: {str(e)}")
    finally:
        # 确保文件句柄被关闭
        if 'file' in files:
            files['file'].close()


def file_upload2url(
        file_path: Annotated[List[str], '本地图片的绝对路径 支持多个']
) -> Dict[str, Any]:
    """
    MCP工具函数：批量上传本地文件并返回所有结果
    
    Args:
        file_path: 本地文件的绝对路径列表
        
    Returns:
        Dict[str, Any]: 包含所有上传结果的字典，格式如下:
        {
            "total": 总文件数,
            "success_count": 成功上传数,
            "failed_count": 失败数,
            "results": [
                {
                    "file_name": 文件名,
                    "file_path": 本地路径,
                    "success": True/False,
                    "file_url": 上传后的URL (成功时),
                    "error": 错误信息 (失败时)
                },
                ...
            ]
        }
    """
    # 如果传入的是单个字符串，转换为列表
    if isinstance(file_path, str):
        file_path = [file_path]
    
    results = []
    success_count = 0
    failed_count = 0
    
    # 逐个上传文件
    for path in file_path:
        file_name = os.path.basename(path)
        result_item = {
            "file_name": file_name,
            "file_path": path
        }
        
        try:
            file_url = upload_file(path)
            result_item["success"] = True
            result_item["file_url"] = file_url
            success_count += 1
        except Exception as e:
            result_item["success"] = False
            result_item["error"] = str(e)
            failed_count += 1
        
        results.append(result_item)
    
    return {
        "total": len(file_path),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }
