"""
该脚本用于生成带有格式化时间戳的Excel文件，并在文件中执行基础操作。
涉及Excel的初始化、单元格操作及文件保存等功能。
"""

import frankyu.tex  # 用于处理特定标点替换的自定义模块
import datetime  # 处理日期和时间
import win32com.client  # 与Windows COM对象交互，用于操作Excel应用程序


def get_current_time() -> datetime.datetime:
    """获取当前的日期和时间对象
    
    Returns:
        datetime.datetime: 表示当前时间的datetime对象
    """
    return datetime.datetime.now()


def format_time(time: datetime.datetime) -> str:
    """将时间对象转换为字符串并替换指定标点符号
    
    Args:
        time (datetime.datetime): 待格式化的时间对象
    
    Returns:
        str: 替换标点后的时间字符串，格式示例：'YYYY年MM月DD日HH时MM分SS秒'
    """
    # 通过自定义模块替换特定标点（将"-", ":", "."替换为中文标点）
    return frankyu.tex.replace_specific_punctuation(
        input_string=str(time),
        punctuation_string=r"-,:,."  # 使用正则表达式指定要替换的标点
    )


def initialize_excel() -> win32com.client.CDispatch:
    """初始化Excel应用程序实例并设置可见性
    
    Returns:
        win32com.client.CDispatch: Excel.Application对象实例
    """
    excel_app = win32com.client.gencache.EnsureDispatch("Excel.Application")
    excel_app.Visible = 1  # 设置Excel窗口可见

    # 禁用所有警告弹窗（如覆盖文件、公式错误等）
    excel_app.DisplayAlerts = False   # 关闭警告提示
    return excel_app


def create_workbook(excel_app: win32com.client.CDispatch) -> win32com.client.CDispatch:
    """在Excel应用中创建新工作簿
    
    Args:
        excel_app (win32com.client.CDispatch): Excel.Application实例
    
    Returns:
        win32com.client.CDispatch: 新建的Workbook对象
    """
    return excel_app.Workbooks.Add()


def get_paste_values_constant() -> int:
    """获取Excel的"粘贴数值"操作常量
    
    Returns:
        int: xlPasteValues常量值(适用于VBA操作中的粘贴选项)
    """
    return win32com.client.constants.xlPasteValues


def get_worksheet(workbook: win32com.client.CDispatch) -> win32com.client.CDispatch:
    """获取工作簿中的第一个工作表
    
    Args:
        workbook (win32com.client.CDispatch): Workbook对象
    
    Returns:
        win32com.client.CDispatch: 第一个Worksheet对象
    """
    return workbook.Worksheets(1)


def get_range(worksheet: win32com.client.CDispatch) -> win32com.client.CDispatch:
    """获取A1:E2单元格区域对象
    
    Args:
        worksheet (win32com.client.CDispatch): Worksheet对象
    
    Returns:
        win32com.client.CDispatch: 表示单元格区域的Range对象
    """
    return worksheet.Range("A1:E2")


def generate_file_name(time_str: str) -> str:
    """生成带时间戳的Excel文件路径
    
    Args:
        time_str (str): 已格式化的时间字符串
    
    Returns:
        str: 完整文件路径，格式示例：'T:\\YYYY年MM月DD日HH时MM分SS秒.xlsx'
    """
    return f"T:\\{time_str}.xlsx"


def save_workbook(workbook: win32com.client.CDispatch, file_path: str) -> None:
    """保存工作簿到指定路径
    
    Args:
        workbook (win32com.client.CDispatch): 要保存的Workbook对象
        file_path (str): 目标文件路径
    """
    workbook.SaveAs(file_path)


def update_single_cell(worksheet: win32com.client.CDispatch, content: str) -> None:
    """在D1单元格写入指定内容
    
    Args:
        worksheet (win32com.client.CDispatch): 目标Worksheet对象
        content (str): 要写入单元格的内容
    """
    worksheet.Range("D1").Value = content


def print_range_values(target_range: win32com.client.CDispatch) -> None:
    """打印单元格区域的值
    
    Args:
        target_range (win32com.client.CDispatch): 包含单元格数据的Range对象
    """
    # 关键修正点：直接使用Range对象的Value属性
    print(list(target_range.Value))


def main():
    """主流程控制函数，协调各模块完成以下操作：
    1. 获取并格式化当前时间
    2. 初始化Excel应用程序
    3. 创建新工作簿并进行基础操作
    4. 生成文件名并保存文件
    5. 更新单元格内容并输出信息
    """
    # 时间处理模块
    current_time = get_current_time()
    formatted_time = format_time(current_time)
    print(f"格式化时间: {formatted_time}")

    # Excel初始化模块
    excel_app = initialize_excel()
    print(f"Excel常量值: {get_paste_values_constant()}")

    # 工作簿操作模块
    workbook = create_workbook(excel_app)
    worksheet = get_worksheet(workbook)
    cell_range = get_range(worksheet)  # 获取Range对象

    # 文件操作模块
    file_path = generate_file_name(formatted_time)
    print(f"文件保存路径: {file_path}")
    save_workbook(workbook, file_path)
    update_single_cell(worksheet, file_path)

    # 信息输出模块
    print_range_values(cell_range)  # 关键修正：传递Range对象而非其Value属性


if __name__ == "__main__":
    main()