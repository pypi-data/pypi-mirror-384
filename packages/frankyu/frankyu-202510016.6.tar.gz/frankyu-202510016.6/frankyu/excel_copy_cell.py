# 导入win32com客户端模块，用于与Excel进行交互
import win32com.client as win32

# 导入os模块，用于文件系统操作（如路径处理和文件删除）
import os

# 从datetime模块导入datetime类，用于生成时间戳
from datetime import datetime

# 导入time模块，用于程序延迟操作
import time

# -------------------------------------------------------------------
# 函数：初始化并配置Excel应用程序
def initialize_excel_application() -> win32.Dispatch:
    """初始化并配置Excel应用程序
    
    Returns:
        win32.Dispatch: Excel应用程序对象
    """
    # 创建Excel应用程序对象
    excel_app = win32.gencache.EnsureDispatch('Excel.Application')
    
    # 设置Excel前台运行（可视化）
    excel_app.Visible = True          # 显示Excel界面
    
    # 禁用所有警告弹窗（如覆盖文件、公式错误等）
    excel_app.DisplayAlerts = False   # 关闭警告提示
    
    # 返回配置好的Excel应用程序对象
    return excel_app

# -------------------------------------------------------------------
# 函数：创建新的Excel工作簿
def create_new_workbook(excel_app: win32.Dispatch) -> win32.Dispatch:
    """创建新的Excel工作簿
    
    Args:
        excel_app (win32.Dispatch): Excel应用程序对象
    
    Returns:
        win32.Dispatch: 新建的工作簿对象
    """
    # 调用Excel的Workbooks.Add方法创建新工作簿
    return excel_app.Workbooks.Add()

# -------------------------------------------------------------------
# 函数：复制指定单元格区域到目标位置
def copy_cell_range(
    worksheet: win32.Dispatch, 
    source_range: str, 
    destination_cell: str
):
    """复制指定单元格区域到目标位置
    
    Args:
        worksheet (win32.Dispatch): 目标工作表对象
        source_range (str): 需要复制的源区域（如"A1:E2"）
        destination_cell (str): 粘贴的目标单元格（如"A5"）
    """
    # 获取源区域对象
    source = worksheet.Range(source_range)
    
    # 获取目标单元格对象
    destination = worksheet.Range(destination_cell)
    
    # 执行复制操作（将源区域内容复制到目标位置）
    source.Copy(Destination=destination)
    
    # 输出复制操作完成信息
    print(f"已复制区域 {source_range} 到 {destination_cell}")

# -------------------------------------------------------------------
# 函数：配置工作表内容（重命名、填充数据、复制内容）
def configure_worksheet_content(workbook: win32.Dispatch):
    """配置工作表内容：重命名、填充数据、复制内容
    
    Args:
        workbook (win32.Dispatch): 需要配置的工作簿对象
    """
    # 获取工作簿的第一个工作表
    main_sheet = workbook.Sheets(1)
    
    # 重命名工作表为"DataSheet"
    main_sheet.Name = 'DataSheet'    # 数据表
    
    # 遍历行索引（1到2行）
    for row in range(1, 3):
        # 遍历列索引（1到5列）
        for col in range(1, 6):
            # 生成单元格值格式（如Row1Col1）
            cell_value = f"Row{row}Col{col}"
            
            # 将生成的值写入当前单元格
            main_sheet.Cells(row, col).Value = cell_value
    
    # 调用独立函数执行复制操作
    copy_cell_range(
        worksheet=main_sheet,
        source_range="A1:E2",
        destination_cell="A5"
    )
    
    # 添加新工作表（用于汇总）
    new_sheet = workbook.Worksheets.Add()
    
    # 重命名新工作表为"SummarySheet"
    new_sheet.Name = 'SummarySheet'  # 汇总表

# -------------------------------------------------------------------
# 函数：生成带时间戳的文件名
def generate_timestamped_filename(base_dir: str = "T:\\") -> str:
    """生成带时间戳的唯一文件名
    
    Args:
        base_dir (str, optional): 文件保存根目录. 默认为 "T:\\"
    
    Returns:
        str: 完整文件路径（包含时间戳）
    """
    # 获取当前时间并格式化为"YYYYMMDD_HHMMSS"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 生成文件名格式（如Report_20231005_143025.xlsx）
    filename = f"Report_{timestamp}.xlsx"
    
    # 合并根目录和文件名，返回完整路径
    return os.path.join(base_dir, filename)

# -------------------------------------------------------------------
# 函数：保存工作簿到指定路径
def save_workbook(workbook: win32.Dispatch, output_path: str):
    """保存工作簿到指定路径
    
    Args:
        workbook (win32.Dispatch): 需要保存的工作簿对象
        output_path (str): 文件保存的完整路径
    """
    # 检查文件是否存在
    if os.path.exists(output_path):
        # 强制删除旧文件（如果存在）
        os.remove(output_path)  
        
    # 保存工作簿到指定路径
    workbook.SaveAs(output_path)
    
    # 输出文件保存路径信息
    print(f"文件已保存至: {output_path}")

# -------------------------------------------------------------------
# 函数：延后关闭Excel应用程序
def close_excel_application(excel_app: win32.Dispatch, delay: int = 30):
    """延后关闭Excel应用程序
    
    Args:
        excel_app (win32.Dispatch): Excel应用程序对象
        delay (int, optional): 关闭前的等待时间（秒）. 默认30秒
    """
    # 输出关闭倒计时信息
    print(f"将在{delay}秒后关闭Excel...")
    
    # 暂停程序执行，等待用户查看结果
    time.sleep(delay)
    
    # 关闭Excel应用程序
    excel_app.Quit()
    
    # 输出关闭完成信息
    print("Excel已关闭")

# -------------------------------------------------------------------
# 主函数：程序入口
def main():
    """程序主函数：协调各功能模块"""
    # 初始化Excel应用程序对象（初始值为None）
    excel_app = None
    
    # 初始化工作簿对象（初始值为None）
    workbook = None
    
    try:
        # 1. 初始化Excel（前台运行）
        # 调用初始化函数获取Excel对象
        excel_app = initialize_excel_application()
        
        # 2. 创建新工作簿
        # 调用创建函数获取新工作簿对象
        workbook = create_new_workbook(excel_app)
        
        # 3. 配置工作表内容
        # 调用配置函数设置工作表数据
        configure_worksheet_content(workbook)
        
        # 4. 生成带时间戳的文件路径
        # 调用生成文件名函数获取保存路径
        output_path = generate_timestamped_filename()
        
        # 5. 保存工作簿
        # 调用保存函数将数据保存到指定路径
        save_workbook(workbook, output_path)

    except Exception as e:
        # 捕获异常并输出错误信息
        print(f"错误：{str(e)}")
    finally:
        # 安全关闭Excel（无论是否发生异常）
        if excel_app:
            # 调用关闭函数终止Excel进程
            close_excel_application(excel_app)

if __name__ == "__main__":
    # 程序入口，仅当直接运行脚本时执行
    main()