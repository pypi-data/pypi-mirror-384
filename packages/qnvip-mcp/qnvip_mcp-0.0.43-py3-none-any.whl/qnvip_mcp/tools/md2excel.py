import pandas as pd
import re
import sys
from openpyxl.styles import Alignment
from typing import Annotated,List

class MarkdownConverter:
    @staticmethod
    def _markdown_table_to_dataframe(md_content: str) -> pd.DataFrame:
        """
        将Markdown格式的表格文本转换为pandas DataFrame。
        """
        # 按行分割
        lines = md_content.strip().split('\n')

        # 移除以 # 开头的行（标题行）
        lines = [line for line in lines if not line.strip().startswith('#')]
        lines = [line for line in lines if len(line)>0 ]

        if len(lines) < 2:
            return pd.DataFrame()

        # 提取表头
        header_line = lines[0]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]

        # 提取数据行
        data = []
        for line in lines[2:]:  # 跳过表头和分隔线
            if '|' not in line:
                continue
            # 使用正则表达式来处理可能存在的行内`|`
            row = [r.strip().replace('<br>', '\n').replace('<br />', '\n').replace('<br/>', '\n') for r in re.split(r'\s*\|\s*', line)]
 
            # 移除行首和行尾的空字符串（因为Markdown表格每行都以|开头和结尾）
            if row and row[0] == '':
                row = row[1:]
            if row and row[-1] == '':
                row = row[:-1]

            # 确保行数据和表头长度一致
            if len(row) == len(headers):
                data.append(row)

        df = pd.DataFrame(data, columns=headers)
        return df



    @staticmethod
    def convert_md_to_excel(md_file_path: Annotated[str, '需要转成excel的本地md的绝对路径'],
                            output_excel_path: Annotated[str, '输出的绝对路径']):
        """
        读取Markdown文件，将其中的表格转换为格式化的Excel文件。
        :param md_file_path: 输入的Markdown文件路径。
        :param output_excel_path: 输出的Excel文件路径。
        """
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            df = MarkdownConverter._markdown_table_to_dataframe(md_content)

            if not df.empty:
                with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                    worksheet = writer.sheets['Sheet1']

                    # 自动调整列宽
                    for column_cells in worksheet.columns:
                        max_length = 0
                        column_letter = column_cells[0].column_letter
                        for cell in column_cells:
                            if cell.value:
                                cell_text = str(cell.value)
                                for line in cell_text.split('\n'):
                                    if len(line) > max_length:
                                        max_length = len(line)
                        adjusted_width = (max_length + 2) * 1.2
                        worksheet.column_dimensions[column_letter].width = adjusted_width

                    # 设置自动换行和顶端对齐
                    for row in worksheet.iter_rows():
                        for cell in row:
                            cell.alignment = Alignment(wrap_text=True, vertical='top')

                print(f"成功将 '{md_file_path}' 转换为 Excel 文件")
            else:
                print(f"在 '{md_file_path}' 中未找到有效的表格数据。")

        except FileNotFoundError:
            print(f"错误: 文件 '{md_file_path}' 未找到。")
        except Exception as e:
            print(f"发生错误: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        # 命令行参数模式：python md2excel.py input.md output.xlsx
        md_file_path = sys.argv[1]
        output_excel_path = sys.argv[2]
    elif len(sys.argv) == 1:
        # 默认模式：无参数时使用默认路径
        md_file_path = '../new_testcase.md'
        output_excel_path = '../new.xlsx'
    else:
        print("使用方法:")
        print("  python md2excel.py <输入的markdown文件> <输出的excel文件>")
        print("  例如: python md2excel.py new_testcase.md output.xlsx")
        print("  或者: python pkg/md2excel.py new_testcase.md \"租-刷单商品配置.xlsx\"")
        sys.exit(1)
    
    MarkdownConverter.convert_md_to_excel(md_file_path, output_excel_path)
