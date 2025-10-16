import platform  # 导入 platform 模块，用于检测操作系统类型
import os  # 导入 os 模块，用于文件路径操作，例如创建目录
from datetime import datetime  # 从 datetime 模块导入 datetime 类，用于生成精确的时间戳
import win32com.client as win32 # 导入 pywin32 库的 win32com.client 模块，用于与 COM 对象（如 Excel）交互

# --- 常量定义 ---
# 定义 Excel 文件在 D 盘上的默认存放目录
DEFAULT_DIR = "D:\\Excel自动化文件"
# 生成一个高度详细的时间戳，格式为：年月日_时分秒_微秒 (例如: 20231027_153045_123456)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
# 默认的文件名，包含详细时间戳，确保每次新建文件名的唯一性
DEFAULT_FILE_NAME = f"自动生成Excel_{TIMESTAMP}.xlsx"
# 完整的默认文件路径，通过 os.path.join 智能拼接目录和文件名
DEFAULT_FILE_PATH = os.path.join(DEFAULT_DIR, DEFAULT_FILE_NAME)


# --- 辅助函数 ---

def _get_excel_application(visible: bool = True):
    """
    获取或启动 Excel 应用程序实例。

    Args:
        visible (bool): 控制 Excel 应用程序窗口是否可见。默认为 True (可见)。

    Returns:
        win32com.client.Dispatch: Excel 应用程序对象。

    Raises:
        ConnectionError: 如果无法启动或连接到 Excel 应用程序，则抛出此错误。
    """
    try:
        # 尝试连接到已经运行的 Excel 应用程序实例
        excel = win32.GetActiveObject("Excel.Application")
    except Exception as e:
        # 如果没有找到运行中的 Excel 实例，则尝试启动一个新的 Excel 进程
        try:
            excel = win32.Dispatch("Excel.Application")
        except Exception as dispatch_e:
            # 如果连启动 Excel 都失败，可能是 Excel 未安装或存在 COM 问题
            raise ConnectionError(f"无法启动或连接到 Excel 应用程序。请确保 Excel 已正确安装。错误详情: {dispatch_e}") from e

    # 根据传入的 visible 参数设置 Excel 应用程序窗口的可见性
    excel.Visible = visible

    # 返回获取到的 Excel 应用程序对象
    return excel


def _open_or_create_excel_workbook(excel_app, file_path: str):
    """
    打开指定的 Excel 工作簿。如果文件不存在，则新建一个。

    Args:
        excel_app: Excel 应用程序实例。
        file_path (str): Excel 文件的完整路径。

    Returns:
        win32com.client.Dispatch: 已打开或新建的工作簿对象。

    Raises:
        Exception: 如果在打开或新建工作簿时发生其他任何错误。
    """
    # 检查文件路径是否存在于文件系统中
    if not os.path.exists(file_path):
        print(f"文件 '{file_path}' 不存在，正在新建一个空白 Excel 工作簿...")
        try:
            # 从文件路径中提取目录名
            dir_name = os.path.dirname(file_path)
            # 如果目录名不为空且该目录不存在，则尝试创建它 (makedirs 可以创建多级目录)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)
                print(f"已创建目录: {dir_name}")
            # 使用 Excel 应用程序对象新建一个空白工作簿
            workbook = excel_app.Workbooks.Add()
            # 立即将新建的工作簿保存到指定的路径
            workbook.SaveAs(file_path)
            print(f"已成功新建文件: {file_path}")
            return workbook
        except Exception as e:
            # 捕获新建文件时可能发生的错误，并抛出自定义异常
            raise Exception(f"新建 Excel 文件 '{file_path}' 时发生错误。请检查路径权限。错误详情: {e}")
    else:
        # 如果文件已经存在，则尝试打开它
        try:
            # 以非只读模式打开工作簿，因为我们打算对其进行修改（删除行）
            return excel_app.Workbooks.Open(file_path, ReadOnly=False)
        except Exception as e:
            # 捕获打开工作簿时可能发生的 COM 错误，并抛出自定义异常
            raise Exception(f"打开工作簿 '{file_path}' 时发生错误。请确保文件未被占用且格式正确。错误详情: {e}")


def _get_excel_worksheet(workbook, sheet_name: str = None):
    """
    获取指定名称的工作表或活动工作表。

    Args:
        workbook: 工作簿对象。
        sheet_name (str, optional): 要获取的工作表的名称。如果为 None，则返回当前活动的工作表。默认为 None。

    Returns:
        win32com.client.Dispatch: 获取到的工作表对象。

    Raises:
        ValueError: 如果指定的工作表名称不存在，或者工作簿中没有活动工作表。
    """
    # 检查是否指定了工作表名称
    if sheet_name:
        try:
            # 尝试通过名称从工作簿中获取指定的工作表
            return workbook.Sheets(sheet_name)
        except Exception:
            # 如果指定名称的工作表不存在，则抛出 ValueError 异常
            raise ValueError(f"错误：工作簿中不存在名为 '{sheet_name}' 的工作表。")
    # 如果没有指定工作表名称
    else:
        # 获取当前活动的工作表
        worksheet = workbook.ActiveSheet
        # 如果工作簿中没有活动的工作表（例如，刚新建的工作簿可能没有默认激活的表）
        if not worksheet:
            # 抛出 ValueError 异常
            raise ValueError("错误：工作簿中没有活动工作表。")
        # 返回获取到的活动工作表对象
        return worksheet


def _delete_rows(worksheet, start_row: int = 1, end_row: int = 5, shift_direction: int = -4162):
    """
    删除指定工作表中指定范围的行。

    Args:
        worksheet: 工作表对象。
        start_row (int): 要删除的起始行号（包含）。默认为 1。
        end_row (int): 要删除的结束行号（包含）。默认为 5。
        shift_direction (int): 删除后单元格的移动方向。默认为 -4162 (xlUp，即向上移动)。
                                 另一个常用的选项是 -4157 (xlToLeft，向左移动，但通常用于列删除)。

    Raises:
        ValueError: 如果行范围无效 (例如，end_row 小于 start_row 或 start_row 小于 1)。
        Exception: 如果在执行删除操作时发生其他 COM 错误。
    """
    # 检查行范围的有效性
    if start_row > end_row or start_row < 1:
        # 如果行范围无效，则抛出 ValueError 异常
        raise ValueError(f"无效的行范围：起始行 {start_row} 必须大于 0 且不大于结束行 {end_row}。")

    try:
        # 构造要删除的行范围字符串，例如 "1:5"
        rows_range = f"{start_row}:{end_row}"
        # 获取该行范围对应的 Range 对象
        rows_to_delete = worksheet.Range(rows_range)
        # 执行删除操作，并指定删除后单元格的移动方向
        rows_to_delete.Delete(shift_direction)
    except Exception as e:
        # 捕获删除操作时可能发生的 COM 错误，并抛出自定义异常
        raise Exception(f"删除行 {start_row} 到 {end_row} 时发生错误。错误详情: {e}")


# --- 主函数 ---

def delete_excel_rows_main(file_path: str = DEFAULT_FILE_PATH, sheet_name: str = None,
                          start_row: int = 1, end_row: int = 5,
                          excel_visible: bool = True, save_changes: bool = True):
    """
    管理整个 Excel 行删除流程。

    此函数会打开指定的 Excel 文件（如果文件不存在则新建一个），
    在指定的工作表（或当前活动工作表）中，删除从 start_row 到 end_row 的行，
    然后根据参数决定是否保存并关闭工作簿。

    Args:
        file_path (str, optional): 要操作的 Excel 文件的完整路径。
                                     默认为 D 盘上的一个带时间戳的默认文件。
        sheet_name (str, optional): 要操作的工作表名称。如果为 None，则默认为活动工作表。
        start_row (int, optional): 要删除的起始行号（包含）。默认为 1。
        end_row (int, optional): 要删除的结束行号（包含）。默认为 5。
        excel_visible (bool, optional): 控制 Excel 应用程序窗口是否可见。默认为 True。
        save_changes (bool, optional): 删除操作完成后是否保存对工作簿的更改。默认为 True。
    """
    # 平台检测：确保此脚本只在 Windows 操作系统上运行，因为 pywin32 是 Windows 特有的库
    if platform.system() != "Windows":
        print("错误: 此脚本依赖于 pywin32 库，只能在 Windows 操作系统上运行。")
        return # 在非 Windows 系统上直接退出函数，不执行后续操作

    excel = None  # 初始化 Excel 应用程序对象为 None
    workbook = None  # 初始化工作簿对象为 None

    try:
        # 步骤 1: 获取 Excel 应用程序实例，并根据 excel_visible 参数设置其可见性
        #excel = _get_excel_application(visible=excel_visible)
        excel = _get_excel_application()

        # 步骤 2: 打开或新建指定的工作簿
        # 如果文件不存在，_open_or_create_excel_workbook 会创建它
        workbook = _open_or_create_excel_workbook(excel, file_path)

        # 步骤 3: 获取要操作的工作表
        worksheet = _get_excel_worksheet(workbook, sheet_name)

        # 步骤 4: 执行行删除操作
        _delete_rows(worksheet, start_row, end_row)

        # 打印操作成功的消息，包含文件路径、工作表名称和删除的行范围信息
        print(f"操作成功：在文件 '{file_path}' 的工作表 '{worksheet.Name}' 中，"
              f"行 {start_row} 到 {end_row} 已成功删除。")

        # 根据 save_changes 参数决定是否保存对工作簿的更改，并关闭工作簿
        # SaveChanges=True 表示保存，SaveChanges=False 表示不保存
        #workbook.Close(SaveChanges=save_changes)

    # 捕获所有自定义或预期的错误，例如连接错误、文件未找到错误、值错误以及其他通用异常
    except (ConnectionError, FileNotFoundError, ValueError, Exception) as e:
        # 打印操作失败的错误信息
        print(f"操作失败：{e}")
        # 如果工作簿在错误发生前已打开，则不保存任何更改并关闭它，以避免数据损坏
        if workbook:
            pass
            #workbook.Close(SaveChanges=False)

    # finally 块确保在 try-except 块结束后执行，无论是否发生异常
    finally:
        # 如果 Excel 应用程序对象存在，则安全地退出 Excel 应用程序
        if excel:
            pass
            #excel.Quit()

