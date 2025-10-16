#!/usr/bin/env python
# coding: utf-8

# In[1]:


import win32com.client
import os
import time
import subprocess # 导入 subprocess 模块

def process_excel_with_r1c1(
    workbook_path=None,
    sheet_name="Sheet1",
    data_to_write=[("A1", "Header"), ("B2", 100)],
    r1c1_formulas_to_set=[("C1", "=SUM(R2C2:R2C2)")],
    excel_visible=True,
    save_workbook=False,
    save_path=None,
    close_workbook=0, # 默认值改为 True 更符合清理资源的意图
    quit_excel=0,     # 默认值改为 True 更符合清理资源的意图
    kill_existing_excel=False # 新增参数，默认不终止现有进程
):
    """
    使用 pywin32 操作 Excel 工作簿，写入数据和设置 R1C1 样式的公式。

    Args:
        data_to_write (list, optional): 要写入的数据列表。每个元素是一个元组 (range_str, value)。
                                        例如：[("A1", "Header"), ("B2", 100)]。默认 None。
        r1c1_formulas_to_set (list, optional): 要设置的 R1C1 公式列表。每个元素是一个元组 (range_str, r1c1_formula_str)。
                                              例如：[("C1", "=SUM(R1C1:R5C1)")]。默认 None。
        workbook_path (str, optional): 要打开的现有 Excel 文件路径。如果为 None，则创建一个新的工作簿。默认 None。
        sheet_name (str): 要操作的工作表名称。如果工作表不存在，此函数可能会出错（取决于 Excel COM 对象的行为）。默认 "Sheet1"。
        excel_visible (bool): 控制 Excel 应用程序是否可见。默认为 True。
        save_workbook (bool): 是否保存工作簿。默认为 False。
        save_path (str, optional): 如果 save_workbook 为 True，指定保存文件的完整路径。
                                    如果 save_workbook 为 True 但 save_path 为 None 且是新创建的工作簿，
                                    将尝试保存到当前目录下的一个临时文件名。默认 None。
        close_workbook (bool): 是否在操作完成后关闭工作簿。默认为 True。
        quit_excel (bool): 是否在操作完成后退出 Excel 应用程序。默认为 True。
        kill_existing_excel (bool): 如果为 True，则在开始处理之前强制终止所有正在运行的 EXCEL.EXE 进程。默认为 False。

    Returns:
        tuple: 包含 Excel 应用程序对象 (excel), 工作簿对象 (workbook), 工作表对象 (sheet)。
               如果 quit_excel 为 True，则返回 (None, None, None)，因为对象已被释放。
               返回这些对象是为了允许在函数外部进行更复杂的操作（如 AutoFill）。
               如果发生错误且对象未成功创建/清理，也可能返回 None。
    """
    excel = None
    workbook = None
    sheet = None

    # --- 新增的逻辑：终止现有 Excel 进程 ---
    if kill_existing_excel:
        print("尝试终止现有 EXCEL.EXE 进程...")
        try:
            # 使用 taskkill 命令强制终止所有 EXCEL.EXE 进程
            # /F: Force termination
            # /IM: Image name (process name)
            # check=False: 即使没有找到进程或发生其他非致命错误，也不抛出异常
            # capture_output=True: 捕获命令的输出，避免直接打印到控制台
            result = subprocess.run(['taskkill', '/F', '/IM', 'EXCEL.EXE'], check=False, capture_output=True, text=True, encoding='gbk')
            print("Taskkill 命令执行完毕。注意：如果没有 Excel 进程运行，可能会显示错误信息，这是正常的。")
            # print(f"Taskkill stdout: {result.stdout}") # 如果需要查看 taskkill 的详细输出可以取消注释
            # print(f"Taskkill stderr: {result.stderr}")
            # 给系统一点时间来完全终止进程
            time.sleep(1)
        except FileNotFoundError:
            print("错误：找不到 taskkill 命令。请确认您是否在 Windows 系统上运行此脚本。")
        except Exception as e:
            print(f"尝试终止 Excel 进程时发生错误: {e}")
    # --- 新增逻辑结束 ---

    try:
        # 创建或获取 Excel 应用程序对象
        # 如果上面成功终止了现有进程，这里通常会启动一个新的 Excel 实例
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = excel_visible
        excel.DisplayAlerts = False

        # 打开现有工作簿或创建新工作簿
        if workbook_path and os.path.exists(workbook_path):
            print(f"正在打开工作簿: {workbook_path}")
            workbook = excel.Workbooks.Open(workbook_path)
            # 确保工作簿不是只读的，如果需要保存的话
            if save_workbook and workbook.ReadOnly:
                 print(f"警告: 工作簿 '{workbook_path}' 是只读的。保存可能会失败。")
                 # 可以选择另存为，或者抛出错误，这里仅警告
        else:
            if workbook_path:
                 print(f"警告: 工作簿 '{workbook_path}' 未找到。改为创建一个新的工作簿。")
            print("正在创建一个新的工作簿。")
            workbook = excel.Workbooks.Add()

        # 获取工作表
        try:
            sheet = workbook.Sheets(sheet_name)
            print(f"正在使用工作表: {sheet_name}")
        except Exception as e:
            print(f"获取工作表 '{sheet_name}' 时出错: {e}")
            print("回退到第一个工作表。")
            sheet = workbook.Sheets(1) # 如果指定的工作表不存在，则使用第一个工作表

        # 写入数据
        if data_to_write:
            print("正在写入数据...")
            for range_str, value in data_to_write:
                try:
                    sheet.Range(range_str).Value = value
                    # print(f"写入 '{value}' 到 {range_str}")
                except Exception as e:
                    print(f"写入 '{value}' 到范围 '{range_str}' 时出错: {e}")

        # 设置 R1C1 公式
        if r1c1_formulas_to_set:
            print("正在设置 R1C1 公式...")
            for range_str, r1c1_formula_str in r1c1_formulas_to_set:
                try:
                    sheet.Range(range_str).FormulaR1C1 = r1c1_formula_str
                    # print(f"设置公式 '{r1c1_formula_str}' 到 {range_str}")
                except Exception as e:
                     print(f"设置公式 '{r1c1_formula_str}' 到范围 '{range_str}' 时出错: {e}")

        # 保存工作簿
        if save_workbook:
            if save_path:
                full_save_path = os.path.abspath(save_path) # 获取绝对路径
            elif workbook_path:
                 full_save_path = os.path.abspath(workbook_path) # 如果是打开的现有工作簿，默认保存回原路径
            else:
                # 如果是新工作簿且没有指定保存路径，生成一个临时文件名
                temp_dir = os.getcwd() # 保存到当前工作目录
                temp_filename = f"temp_excel_{int(time.time())}.xlsx"
                full_save_path = os.path.join(temp_dir, temp_filename)
                print(f"新工作簿未指定 save_path。将保存到临时文件: {full_save_path}")

            try:
                # xlWorkbookDefault = 51 (for .xlsx format)
                # FileFormat 参数指定文件格式，避免兼容性警告
                workbook.SaveAs(full_save_path, FileFormat=51)
                print(f"工作簿已保存到: {full_save_path}")
            except Exception as e:
                print(f"保存工作簿到 '{full_save_path}' 时出错: {e}")
                # 如果保存失败，可能需要用户手动处理

    except Exception as e:
        print(f"在 Excel 处理过程中发生错误: {e}")
        # 发生其他未知错误

    finally:
        # 清理资源
        # 确保对象存在且有效，避免在出错时再次引用 None 或无效对象
        if workbook is not None:
            if close_workbook:
                try:
                    # 根据是否需要保存来关闭工作簿
                    workbook.Close(SaveChanges=save_workbook)
                    print("工作簿已关闭。")
                except Exception as e:
                    print(f"关闭工作簿时出错: {e}")
            # 在关闭工作簿后显式释放 COM 对象引用 (虽然 Python 的垃圾回收会处理，但显式释放有时有帮助)
            # workbook = None # 也可以考虑在这里置为 None

        if excel is not None:
            if quit_excel:
                try:
                    excel.Quit()
                    print("Excel 已退出。")
                except Exception as e:
                    print(f"退出 Excel 时出错: {e}")
            # 在退出 Excel 后显式释放 COM 对象引用
            # excel = None # 也可以考虑在这里置为 None

        # 返回对象，除非已退出 Excel
        # 只有在 quit_excel 为 False 且 excel 对象成功创建时才返回有效的对象
        if not quit_excel and excel is not None:
            return excel, workbook, sheet
        else:
            # 如果 Excel 已退出或未成功创建，COM 对象可能无效，返回 None
            return None, None, None


# In[2]:


import datetime
from typing import Optional, Tuple, Any

def create_new_excel_workbook(
    base_name: str = "workbook",
    cloud_storage_path: str = r'https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/xls/',
    local_storage_path: str = "T:\\xls\\",
    use_cloud_storage: bool = False,
    data_to_write: Optional[list] = None,
    r1c1_formulas_to_set: Optional[list] = None,
    kill_existing_excel: bool = 0,
    quit_excel_after_creation: bool = False,
    close_workbook_after_creation: bool = False,
    save_workbook: bool = True,
    excel_visible: bool = True,
    file_extension: str = ".xlsx",
    timestamp_format: str = "%Y%m%d%H%M%S%f",
    overwrite_existing: bool = False
) -> Tuple[Any, Any, Any]:
    """
    创建一个带有时间戳文件名的新Excel工作簿，并可选择写入数据和公式
    
    参数:
        base_name: 工作簿基础名称，默认为"workbook"
        cloud_storage_path: 云存储路径，默认为OneDrive路径
        local_storage_path: 本地存储路径，默认为"T:\\xls\\"
        use_cloud_storage: 是否使用云存储路径，默认为False(使用本地)
        data_to_write: 要写入的数据列表[(单元格范围, 值), ...]，默认为None
        r1c1_formulas_to_set: 要设置的R1C1公式列表[(单元格范围, 公式), ...]，默认为None
        kill_existing_excel: 是否终止现有的Excel进程，默认为True
        quit_excel_after_creation: 创建后是否退出Excel，默认为False
        close_workbook_after_creation: 创建后是否关闭工作簿，默认为False
        save_workbook: 是否保存工作簿，默认为True
        excel_visible: Excel是否可见，默认为True
        file_extension: 文件扩展名，默认为".xlsx"
        timestamp_format: 时间戳格式，默认为"%Y%m%d%H%M%S%f"
        overwrite_existing: 如果文件存在是否覆盖，默认为False
        
    返回:
        元组: (Excel应用对象, 工作簿对象, 工作表对象) 如果已退出则返回(None, None, None)
    """
    try:
        # 生成时间戳
        timestamp = datetime.datetime.now().strftime(timestamp_format)
        
        # 确定存储路径
        storage_path = cloud_storage_path if use_cloud_storage else local_storage_path
        
        # 创建完整文件路径
        filename = f"{base_name}_{timestamp}{file_extension}"
        full_path = storage_path + filename
        
        print(f"正在创建新工作簿: {full_path}")
        
        # 检查文件是否存在(如果不允许覆盖)
        if not overwrite_existing and os.path.exists(full_path):
            raise FileExistsError(f"文件已存在: {full_path}")
        
        # 创建工作簿
        excel_app, workbook, worksheet = process_excel_with_r1c1(
            kill_existing_excel=kill_existing_excel,
            data_to_write=data_to_write,
            quit_excel=quit_excel_after_creation,
            r1c1_formulas_to_set=r1c1_formulas_to_set,
            close_workbook=close_workbook_after_creation,
            save_path=full_path,
            save_workbook=save_workbook,
            excel_visible=excel_visible
        )
        
        return excel_app, workbook, worksheet
        
    except FileExistsError as fee:
        print(f"错误: {fee}")
        return None, None, None
    except Exception as e:
        print(f"创建工作簿时发生意外错误: {e}")
        return None, None, None


 


# In[3]:


if __name__ == "__main__":

    bbb = create_new_excel_workbook("工作日志")
    input()


# In[ ]:





# In[ ]:




