import pandas as pd
import webbrowser
import sys
import os
import time # 导入 time 模块

def open_excel_links(excel_path):
    """
    在默认网页浏览器中打开 Excel 文件（C2 到 C99 单元格）中的 URL，每次打开之间有 1 秒延迟。

    参数:
        excel_path (str): Excel 文件的路径（.xls 或 .xlsx）。
    """
    if not os.path.exists(excel_path):
        print(f"错误：文件 '{excel_path}' 不存在。")
        return

    try:
        if excel_path.endswith('.xlsx'):
            df = pd.read_excel(excel_path, engine='openpyxl')
        elif excel_path.endswith('.xls'):
            df = pd.read_excel(excel_path, engine='xlrd')
        else:
            print("错误：文件格式不受支持。请提供 .xls 或 .xlsx 文件。")
            return
    except Exception as e:
        print(f"读取 Excel 文件时出错：{e}")
        print("请确保这是一个有效的 .xls 或 .xlsx 文件，并且没有损坏。")
        return

    if 'C' not in df.columns:
        if len(df.columns) < 3:
            print("错误：在 Excel 文件中找不到 'C' 列或第三列。")
            print("请确保您的链接位于 C 列。")
            return
        column_to_check = df.columns[2]
        print(f"警告：未找到名为 'C' 的列。将使用第三列（列名：'{column_to_check}'）。")
    else:
        column_to_check = 'C'

    end_row_index = min(98, len(df) - 1)

    links_opened = 0
    print(f"尝试打开 C2 到 C{end_row_index + 1} 的链接，每次打开之间有 1 秒延迟...")

    for i in range(1, end_row_index + 1):
        link = df.loc[i, column_to_check]
        if pd.isna(link):
            continue

        link_str = str(link).strip()
        if link_str:
            try:
                webbrowser.open_new_tab(link_str)
                print(f"已打开：{link_str}")
                links_opened += 1
                # 在打开下一个链接之前等待 1 秒
                time.sleep(10) 
            except webbrowser.Error as e:
                print(f"无法打开 '{link_str}'：{e}")
            except Exception as e:
                print(f"处理 '{link_str}' 时发生意外错误：{e}")

    if links_opened == 0:
        print("在指定范围 (C2:C99) 内未找到或未打开任何有效链接。")
    else:
        print(f"已完成打开 {links_opened} 个链接。")

if __name__ == "__main__2":
    if len(sys.argv) < 2:
        print("用法：python 你的脚本名.py <excel_文件路径>")
        print("示例：python open_links.py D:\\文档\\链接.xlsx")
    else:
        excel_file_path = sys.argv[1]
        open_excel_links(excel_file_path)