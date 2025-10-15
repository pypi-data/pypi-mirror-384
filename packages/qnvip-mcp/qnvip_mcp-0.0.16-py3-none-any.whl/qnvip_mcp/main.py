# main.py
from fastmcp import FastMCP
from .tools.dify_qwen_content_search import gen_testcases
from .tools.dify_testcases import testcases_instructions
from .tools.md2excel import MarkdownConverter
from .tools.file_upload import file_upload2url

app = FastMCP("qnvip-qwen-mcp")

# 文件上传
app.tool(description="上传文件，本地上传文件转成upload_file_id的步骤")(file_upload2url)

# 测试用例生成指导
app.tool(description="生成测试用例的todolist,生成测试用例的工作流程和规范的指导,生成测试用例前使用")(testcases_instructions)

# 测试用例生成
app.tool(description="使用搜索查询公司文档，代码规范，技术文档，需求文档，周报，日报，代码，获取原文")(gen_testcases)

# md table转excel
app.tool(description="将Markdown的表格部分文件转换为Excel文件")(MarkdownConverter.convert_md_to_excel)


def main():
    """MCP服务入口点"""
    app.run(transport="stdio")

if __name__ == "__main__":
    main()
