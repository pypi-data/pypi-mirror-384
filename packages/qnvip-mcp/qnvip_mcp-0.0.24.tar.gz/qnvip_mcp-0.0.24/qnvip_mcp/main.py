# main.py
from fastmcp import FastMCP
from .tools.dify_qwen_content_search import search_content
from .tools.dify_testcases import testcases_instructions
from .tools.md2excel import MarkdownConverter
from .tools.file_upload import file_upload2url
from .tools.dify_ai_read_img import ai_read_img

app = FastMCP("qnvip-qwen-mcp")

# 文件上传
app.tool(description="上传文件，批量上传本地文件并返回所有结果")(file_upload2url)

# ai读取图片内容
app.tool(description="使用视觉模型按要求批量读取图片的内容")(ai_read_img)

# 测试用例生成指导
app.tool(description="生成测试用例前必须调用的工具,这里提供生成测试用例的工作流程和规范的指导")(testcases_instructions)

# 搜索千问里的文章
app.tool(description="使用搜索查询公司文档，代码规范，技术文档，需求文档，周报，日报，代码，获取原文")(search_content)

# md table转excel
app.tool(description="将Markdown的表格部分文件转换为Excel文件")(MarkdownConverter.convert_md_to_excel)


def main():
    """MCP服务入口点"""
    app.run(transport="stdio")

if __name__ == "__main__":
    main()
