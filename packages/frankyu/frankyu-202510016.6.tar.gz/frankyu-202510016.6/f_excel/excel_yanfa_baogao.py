#!/usr/bin/env python
# coding: utf-8
# 脚本起始行，指定解释器为 python 并且设置编码为 utf-8

import os  # 导入 os 模块，用于文件和目录操作
import win32com.client  # 导入 win32com.client 模块，用于与 Windows 应用程序（如 Excel）交互
import datetime  # 导入 datetime 模块，用于方便地处理日期


def convert_formula_to_value(sheet, cell_range):
    """
    将指定工作表的单元格范围内的公式转换为值。
    
    方法清单:
    - sheet.Range(cell_range): 获取指定单元格范围。
    - range_obj.Value: 获取单元格的值。
    - range_obj.Value = range_obj.Value: 将单元格值赋值给自身，去除公式。

    Args:
        sheet: Excel 工作表对象。
        cell_range: 要处理的单元格范围字符串 (例如 "B2" 或 "B5:Z100")。

    Returns:
        True 如果处理成功，False 如果处理失败。
    """
    try:
        # 获取指定的单元格范围对象
        range_obj = sheet.Range(cell_range)
        # 将范围内的值赋值给自身，从而去除公式
        range_obj.Value = range_obj.Value
        return True
    except Exception as e:
        # 捕获异常并打印错误信息
        print(f'处理工作表 "{sheet.Name}" 的范围 "{cell_range}" 时出错: {e}')
        return False


def process_excel_formulas(filepath, target_sheet_name="报告", formula_ranges=None):
    """
    去除 Excel 文件中特定单元格区域的公式，将其转换为值。

    方法清单:
    - os.path.exists(filepath): 检查文件是否存在。
    - excel_app.Workbooks.Open(filepath): 打开 Excel 文件。
    - sheet.Range(cell_range): 按范围获取单元格值。
    - workbook.Save(): 保存工作簿更改。

    Args:
        filepath: Excel 文件完整路径。
        target_sheet_name: 要处理的工作表名称，默认为 "报告"。
        formula_ranges: 包含要转换公式为值的单元格范围列表，默认为 ["B2", "B5:Z100"]。

    Returns:
        True 如果处理成功，False 如果处理失败。
    """
    if not os.path.exists(filepath):  # 检查文件是否存在
        print(f'文件不存在: {filepath}')
        return False

    excel_app = None  # 初始化 Excel 应用程序对象为 None
    workbook = None  # 初始化 Excel 工作簿对象为 None
    if formula_ranges is None:  # 如果未提供公式范围，则使用默认值
        formula_ranges = ["B2", "B5:Z100"]

    try:
        # 创建 Excel 应用程序对象
        excel_app = win32com.client.Dispatch('Excel.Application')
        # 设置 Excel 应用程序不可见
        excel_app.Visible = False
        # 打开指定的 Excel 文件
        workbook = excel_app.Workbooks.Open(filepath)
        # 禁用 Excel 的警告提示
        excel_app.DisplayAlerts = False
        # 获取指定名称的工作表
        sheet = workbook.Worksheets(target_sheet_name)

        # 遍历需要处理的单元格范围
        for cell_range in formula_ranges:
            # 调用函数将公式转化为值
            if not convert_formula_to_value(sheet, cell_range):
                return False

        # 保存工作簿
        workbook.Save()
        print(f'{workbook.Name} quCuLianJie OK')
        return True

    except Exception as e:
        # 捕获处理异常并打印详细错误信息
        print(f'处理文件 {filepath} 的公式时出错: {e}')
        return False
    finally:
        # 关闭工作簿和退出 Excel 应用程序以释放资源
        if workbook:
            workbook.Close(False)
        if excel_app:
            excel_app.Quit()


def delete_other_sheets(filepath, target_sheet_name="报告"):
    """
    删除 Excel 文件中除了指定工作表之外的所有其他工作表。

    方法清单:
    - workbook.Worksheets: 遍历所有工作表。
    - sheet.Delete(): 删除工作表。
    - workbook.Save(): 保存工作簿更改。

    Args:
        filepath: Excel 文件完整路径。
        target_sheet_name: 要保留的工作表名称，默认为 "报告"。

    Returns:
        True 如果处理成功，False 如果处理失败。
    """
    if not os.path.exists(filepath):  # 检查文件是否存在
        print(f'文件不存在: {filepath}')
        return False

    excel_app = None  # 初始化 Excel 应用程序对象为 None
    workbook = None  # 初始化 Excel 工作簿对象为 None
    try:
        # 创建 Excel 应用程序对象
        excel_app = win32com.client.Dispatch('Excel.Application')
        # 设置 Excel 应用程序不可见
        excel_app.Visible = False
        # 打开指定的 Excel 文件
        workbook = excel_app.Workbooks.Open(filepath)
        # 禁用 Excel 的警告提示
        excel_app.DisplayAlerts = False

        # 初始化一个列表，用于存储需要删除的工作表
        sheets_to_delete = []
        for sheet in workbook.Worksheets:
            # 如果工作表名称不是目标名称，则添加到删除列表
            if sheet.Name != target_sheet_name:
                sheets_to_delete.append(sheet)

        # 逆序删除，避免索引问题
        for sheet in reversed(sheets_to_delete):
            print(f'正在删除工作表: {sheet.Name}')
            sheet.Delete()

        # 保存工作簿
        workbook.Save()
        print(f'{workbook.Name} canCuSheet OK')
        return True

    except Exception as e:
        # 捕获处理异常并打印详细错误信息
        print(f'处理文件 {filepath} 的工作表时出错: {e}')
        return False
    finally:
        # 关闭工作簿和退出 Excel 应用程序以释放资源
        if workbook:
            workbook.Close(False)
        if excel_app:
            excel_app.Quit()


def find_excel_files(pathroot, file_extension=".xlsx"):
    """
    遍历指定根目录下的所有文件夹和文件，并将所有指定扩展名的文件的完整路径添加到列表中返回。

    方法清单:
    - os.walk(pathroot): 遍历目录树。
    - file.endswith(file_extension): 筛选特定扩展名文件。

    Args:
        pathroot: 根目录路径。
        file_extension: 要查找的文件扩展名，默认为 ".xlsx"。

    Returns:
        包含所有指定扩展名文件完整路径的列表。
    """
    file_list = []
    for root_dir, _, files in os.walk(pathroot):
        for file in files:
            if file.endswith(file_extension):
                file_path = os.path.join(root_dir, file)
                file_list.append(file_path)
    return file_list


def rename_excel_file(excelpath, new_file_prefix="品质检测报告"):
    """
    根据 Excel 文件的路径信息，按照特定规则重命名 Excel 文件。

    方法清单:
    - os.rename(): 重命名文件。
    - os.path.dirname(): 获取文件目录路径。
    - os.path.basename(): 获取文件名。

    Args:
        excelpath: Excel 文件完整路径。
        new_file_prefix: 新文件名的前缀，默认为 "品质检测报告"。

    Returns:
        True 如果重命名成功，False 如果重命名失败。
    """
    month_dict = {
        8: "Aug", 7: "Jul", 1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    path_parts = excelpath.split("\\")
    if len(path_parts) < 2:
        print(f'文件路径格式不正确: {excelpath}')
        return False

    folder_name = path_parts[-2]
    file_name_with_extension = path_parts[-1]

    try:
        month_year_str = folder_name
        year_str_2digit = month_year_str.split(".")[0]
        month_str_2digit = month_year_str.split(".")[1]
        month_int = int(month_str_2digit)
        month_abbr = month_dict.get(month_int)
        if not month_abbr:
            print(f'无法识别的月份: {month_str_2digit}，文件: {excelpath}')
            return False

        file_name_without_extension = file_name_with_extension.split(".")[0]
        folder_path = os.path.dirname(excelpath)

        new_file_name_without_extension = (
            f"{new_file_prefix}{file_name_without_extension}-20{year_str_2digit}-{month_abbr}"
        )
        new_file_name = new_file_name_without_extension + ".xlsx"
        new_file_path = os.path.join(folder_path, new_file_name)

        os.rename(excelpath, new_file_path)
        print(f'{new_file_path} 重命名成功。')
        return True

    except (ValueError, IndexError) as e:
        print(f'解析文件路径或文件名时出错: {e}，文件: {excelpath}')
        return False
    except FileExistsError:
        print(f'文件已存在，无法重命名: {new_file_path}')
        return False
    except Exception as e:
        print(f'重命名文件 {excelpath} 出错: {e}')
        return False


def should_rename(filepath, renamed_keyword="品质"):
    """
    检查文件是否需要重命名。如果文件名中包含指定的关键字，则认为已重命名。

    方法清单:
    - os.path.exists(filepath): 检查文件是否存在。
    - os.path.basename(): 获取文件名。

    Args:
        filepath: Excel 文件完整路径。
        renamed_keyword: 用于判断文件是否已重命名的关键字，默认为 "品质"。

    Returns:
        True 如果文件已重命名或重命名成功，False 如果文件不存在或重命名失败。
    """
    if not os.path.exists(filepath):
        print(f'文件不存在: {filepath}')
        return False

    if renamed_keyword in os.path.basename(filepath):
        print(f'{filepath} 已经完成,无需转化')
        return True
    else:
        return rename_excel_file(filepath)


def process_excel_files(root_path_list, target_filename_length=len(r"2024RD05.xlsx"),
                       target_sheet_name="报告", formula_cell_ranges=None,
                       renamed_check_keyword="品质", new_file_prefix="品质检测报告"):
    """
    遍历指定根目录列表下的所有 Excel 文件，并根据文件名进行处理。

    方法清单:
    - find_excel_files(): 查找 Excel 文件。
    - process_excel_formulas(): 转换单元格公式为值。
    - delete_other_sheets(): 删除非目标工作表。
    - should_rename(): 检查并重命名文件。

    Args:
        root_path_list: 根目录路径列表。
        target_filename_length: 需要处理的文件名的长度，默认为 len("2024RD05.xlsx")。
        target_sheet_name: 要处理的工作表名称，默认为 "报告"。
        formula_cell_ranges: 包含要转换公式为值的单元格范围列表，默认为 ["B2", "B5:Z100"]。
        renamed_check_keyword: 用于判断文件是否已重命名的关键字，默认为 "品质"。
        new_file_prefix: 新文件名的前缀，默认为 "品质检测报告"。
    """
    for root_path in root_path_list:
        print(f'正在处理目录: {root_path}')
        file_list = find_excel_files(root_path)
        if not file_list:
            print(f'目录 {root_path} 中没有找到 Excel 文件')
            continue

        for file_path in file_list:
            if len(os.path.basename(file_path)) == target_filename_length:
                print(f'处理文件: {file_path}')
                if process_excel_formulas(
                    file_path,
                    target_sheet_name=target_sheet_name,
                    formula_ranges=formula_cell_ranges
                ):
                    if delete_other_sheets(file_path, target_sheet_name=target_sheet_name):
                        should_rename(file_path, renamed_keyword=renamed_check_keyword)
                        print(f'{file_path} 处理完成')
                    else:
                        print(f'{file_path} delete_other_sheets 处理失败')
                else:
                    print(f'{file_path} process_excel_formulas 处理失败')
                print(" over")
            else:
                print(f'跳过文件: {file_path}, 文件名格式不符合条件')
        print(f'目录 {root_path} 处理完成')
    print("all over")


if __name__ == "__main__":
    root_directories = [
        r"C:\Users\frank_yu\Downloads\sc26\1348",
        r"D:\新增資料夾\中间数据"
    ]

    report_sheet = "报告"
    formula_cells = ["B2", "B5:Z100"]
    renamed_keyword_check = "品质"
    new_report_prefix = "品质检测报告"
    target_filename_len = len(r"2024RD05.xlsx")

    print("开始处理 Excel 文件...")
    process_excel_files(
        root_directories,
        target_filename_length=target_filename_len,
        target_sheet_name=report_sheet,
        formula_cell_ranges=formula_cells,
        renamed_check_keyword=renamed_keyword_check,
        new_file_prefix=new_report_prefix
    )
    print("所有 Excel 文件处理完成。")
    print("over")