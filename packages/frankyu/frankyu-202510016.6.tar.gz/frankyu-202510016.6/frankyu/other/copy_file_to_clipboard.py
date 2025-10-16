import sys
import os
import time
import datetime
import subprocess

# --- 导入 pywin32 相关的模块，并增加错误处理 ---
try:
    import win32api
    import win32con
    import win32com.client
    import pythoncom # 用于COM对象管理，特别是释放
    from winreg import ConnectRegistry, OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE
    print("pywin32 及相关模块导入成功。")
except ImportError as e:
    print(f"错误: 导入 pywin32 模块失败。请确保已安装 'pywin32' 库。")
    print(f"您可以尝试运行 'pip install pywin32' 来安装。详情: {e}")
    sys.exit(1) # 如果核心库无法导入，程序直接退出

# --- 平台和 Office 版本检测函数 ---

def check_platform(expected_platform="win32"):
    """
    检查当前运行的操作系统平台。

    __doc__: 
        此函数用于检测程序运行的操作系统。
        它返回一个布尔值，指示当前系统是否为 Windows。
        PowerPoint自动化操作仅支持Windows平台。

    Args:
        expected_platform (str): 期望的操作系统平台，默认为 "win32" (Windows)。

    Returns:
        bool: 如果当前平台与期望平台一致则返回True，否则返回False。
    """
    if sys.platform != expected_platform:
        print(f"错误: 此脚本设计为在 {expected_platform.capitalize()} 平台上运行，但当前是 {sys.platform.capitalize()}。")
        return False
    print(f"平台检测: 当前系统为 {expected_platform.capitalize()}。")
    return True

def get_office_version(app_name="PowerPoint.Application"):
    """
    尝试获取已安装的Microsoft Office PowerPoint版本。

    __doc__:
        此函数尝试通过注册表或COM对象获取已安装的Microsoft Office应用程序版本信息。
        它返回一个字符串，包含检测到的应用程序版本，如果未检测到则返回"未知"。
        此检测可能受Office安装类型和系统权限影响。

    Args:
        app_name (str): 要检测的Office应用程序COM名称，默认为 "PowerPoint.Application"。

    Returns:
        str: 检测到的Office应用程序版本字符串，例如 "PowerPoint 16.0 (Office 365)" 或 "未知"。
    """
    version = "未知"
    app_test = None
    try:
        # 尝试通过注册表获取版本信息 (主要针对ClickToRun版本)
        try:
            reg_path = r"SOFTWARE\Microsoft\Office\ClickToRun\O365Client\CurrentVersion"
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as reg:
                with OpenKey(reg, reg_path) as key:
                    product_version, _ = QueryValueEx(key, "ProductVersion")
                    if product_version:
                        version = f"Office ClickToRun (版本: {product_version})"
                        print(f"Office 版本检测 (注册表): {version}")
                        return version
        except Exception:
            pass # 注册表路径可能不存在，继续尝试其他方法

        # 尝试通过COM对象获取版本号
        try:
            app_test = win32com.client.Dispatch(app_name)
            app_version_num = app_test.Version # 获取版本号字符串，如 "16.0"
            
            # 根据版本号映射到常见名称
            if app_version_num.startswith("16.0"):
                version = f"{app_name.split('.')[0]} {app_version_num} (Office 2016/2019/365)"
            elif app_version_num.startswith("15.0"):
                version = f"{app_name.split('.')[0]} {app_version_num} (Office 2013)"
            elif app_version_num.startswith("14.0"):
                version = f"{app_name.split('.')[0]} {app_version_num} (Office 2010)"
            else:
                version = f"{app_name.split('.')[0]} {app_version_num}"
            print(f"Office 版本检测 (COM): {version}")
        except Exception as e:
            print(f"未能通过COM对象获取 {app_name} 版本。这可能是因为 {app_name.split('.')[0]} 未安装或未注册。详情: {e}")
        finally:
            if app_test:
                try:
                    app_test.Quit()
                    if hasattr(app_test, '_oleobj_'):
                        win32api.CoDisconnectObject(app_test._oleobj_)
                    del app_test
                except Exception as e:
                    print(f"警告: 尝试清理测试 {app_name.split('.')[0]} COM对象时发生错误: {e}")
    except Exception as e:
        print(f"Office 版本检测过程中发生意外错误: {e}")
    
    return version

# --- PowerPoint 操作函数 ---

def get_powerpoint_app(visible=True, create_new_if_not_running=True):
    """
    获取或启动PowerPoint应用程序实例。

    __doc__:
        尝试连接到已运行的PowerPoint应用程序实例。
        如果 `create_new_if_not_running` 为 True 且未找到运行实例，则启动一个新的实例。
        根据 `visible` 参数设置PowerPoint应用程序的可见性。
        如果无法连接或启动，则返回None并打印错误信息。

    Args:
        visible (bool): 设置PowerPoint应用程序是否可见，默认为True。
        create_new_if_not_running (bool): 如果没有运行实例，是否创建新的，默认为True。

    Returns:
        win32com.client.Dispatch: PowerPoint应用程序COM对象，如果失败则为None。
    """
    powerpoint_app = None
    try:
        # 尝试连接到已运行的实例
        powerpoint_app = win32com.client.GetActiveObject("PowerPoint.Application")
        print("已连接到正在运行的PowerPoint应用程序。")
    except Exception:
        # 如果没有运行实例且允许创建新的
        if create_new_if_not_running:
            try:
                powerpoint_app = win32com.client.Dispatch("PowerPoint.Application")
                print("已启动新的PowerPoint应用程序实例。")
            except Exception as e:
                print(f"错误: 无法启动PowerPoint应用程序。请确保已安装Office PowerPoint。详情: {e}")
                return None
        else:
            print("错误: 没有运行的PowerPoint实例，且不允许创建新的实例。")
            return None
            
    if powerpoint_app:
        try:
            powerpoint_app.Visible = visible # 根据参数设置可见性
            return powerpoint_app
        except Exception as e:
            print(f"警告: 无法设置PowerPoint应用程序可见性。详情: {e}")
            return powerpoint_app # 仍然返回应用对象，可能不影响核心功能
    return None

def get_active_presentation(app, require_active=True):
    """
    获取当前PowerPoint应用程序中活跃的演示文稿。

    __doc__:
        检查PowerPoint应用程序中是否有打开的演示文稿。
        如果 `require_active` 为 True 且没有活跃的演示文稿，则返回None。
        如果存在，则返回当前活跃的演示文稿对象。
        如果没有打开的演示文稿或发生错误，则返回None并打印相应的提示或错误信息。

    Args:
        app (win32com.client.Dispatch): PowerPoint应用程序COM对象。
        require_active (bool): 是否强制要求存在活跃的演示文稿，默认为True。

    Returns:
        win32com.client.CDispatch: 当前活跃的演示文稿COM对象，如果失败则为None。
    """
    if not app:
        print("错误: PowerPoint应用程序对象无效，无法获取演示文稿。")
        return None
    
    try:
        if app.Presentations.Count == 0:
            if require_active:
                print("错误: 没有打开的演示文稿。请打开一个PowerPoint文件并确保它是活跃窗口。")
                return None
            else:
                print("警告: 没有打开的演示文稿，但未强制要求活跃演示文稿。")
                return None # 或者可以返回一个空列表/None，取决于后续逻辑
        return app.ActivePresentation
    except Exception as e:
        print(f"错误: 获取当前活跃演示文稿时发生错误。详情: {e}")
        return None

def generate_timestamped_filepath(presentation, directory="D:\\", 
                                  filename_prefix=None, timestamp_format="%Y%m%d_%H%M%S", 
                                  file_extension=".pptx"):
    """
    生成一个带时间戳的文件保存路径。

    __doc__:
        根据传入的演示文稿名称（或指定前缀）、当前时间戳和文件扩展名，
        生成一个新的文件名，并将其与指定的目录组合，形成完整的保存路径。
        确保目标目录存在，如果不存在则尝试创建。

    Args:
        presentation (win32com.client.CDispatch): PowerPoint演示文稿对象。
        directory (str): 文件保存的目标目录，默认为 "D:\\"。
        filename_prefix (str, optional): 新文件名的前缀。如果为None，则使用原始演示文稿的文件名。
        timestamp_format (str): 时间戳的格式字符串，默认为 "%Y%m%d_%H%M%S"。
        file_extension (str): 保存文件的扩展名，默认为 ".pptx"。

    Returns:
        str: 完整的文件保存路径，如果无法生成则返回None。
    """
    if not presentation:
        print("错误: 演示文稿对象无效，无法生成文件路径。")
        return None
        
    try:
        # 确保目标目录存在
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"已创建目标目录: {directory}")
            except OSError as e:
                print(f"错误: 无法创建目标目录 '{directory}'。请检查权限或路径。详情: {e}")
                return None

        timestamp = datetime.datetime.now().strftime(timestamp_format)
        
        # 确定文件名前缀
        if filename_prefix is None:
            try:
                # 获取原始文件名（不含路径和扩展名）
                original_filename = os.path.splitext(os.path.basename(presentation.FullName))[0]
            except Exception:
                print("警告: 无法获取原始演示文稿文件名，使用默认名称 'Presentation'。")
                original_filename = "Presentation"
            base_name = original_filename
        else:
            base_name = filename_prefix
            
        new_filename = f"{base_name}_{timestamp}{file_extension}"
        new_filepath = os.path.join(directory, new_filename)
        print(f"已生成目标文件路径: {new_filepath}")
        return new_filepath
    except Exception as e:
        print(f"错误: 生成文件路径时发生错误。详情: {e}")
        return None

def save_presentation(presentation, filepath, file_format=None):
    """
    保存演示文稿到指定路径和格式。

    __doc__:
        将传入的PowerPoint演示文稿对象保存到指定的完整文件路径。
        可以指定保存的文件格式，如果未指定，则使用默认格式（通常由文件扩展名决定）。
        如果保存过程中发生任何错误，将打印错误信息并返回False。

    Args:
        presentation (win32com.client.CDispatch): PowerPoint演示文稿对象。
        filepath (str): 文件的完整保存路径。
        file_format (int, optional): PowerPoint文件保存格式的常量。
                                     例如，ppSaveAsOpenXMLPresentation (24) for .pptx。
                                     如果为None，PowerPoint会根据文件扩展名自动选择。

    Returns:
        bool: 如果保存成功则返回True，否则返回False。
    """
    if not presentation or not filepath:
        print("错误: 演示文稿对象或文件路径无效，无法保存。")
        return False
        
    try:
        if file_format is not None:
            # 确保使用正确的保存格式常量
            # win32com.client.constants 可以提供这些常量
            presentation.SaveAs(filepath, file_format)
        else:
            presentation.SaveAs(filepath) # PowerPoint会根据扩展名自动选择格式
        print(f"演示文稿已成功保存到: {filepath}")
        return True
    except Exception as e:
        print(f"错误: 保存演示文稿时发生错误。请检查路径、文件名是否有效或文件是否被占用。详情: {e}")
        return False

def copy_file_to_clipboard(filepath, hide_powershell_window=True):
    """
    将指定文件复制到剪贴板。

    __doc__:
        此函数使用PowerShell命令模拟Windows操作系统中的文件复制操作，
        将指定路径的文件复制到剪贴板，而非仅仅复制文件路径文本。
        如果文件不存在或PowerShell命令执行失败，则返回False。

    Args:
        filepath (str): 要复制的文件的完整路径。
        hide_powershell_window (bool): 是否隐藏PowerShell窗口，默认为True。

    Returns:
        bool: 如果复制成功则返回True，否则返回False。
    """
    if not filepath or not os.path.exists(filepath):
        print(f"错误: 文件 '{filepath}' 不存在或路径无效，无法复制到剪贴板。")
        return False

    try:
        powershell_command = f'Set-Clipboard -LiteralPath "{filepath}"'
        creation_flags = subprocess.CREATE_NO_WINDOW if hide_powershell_window else 0

        subprocess.run(["powershell", "-Command", powershell_command], 
                       check=True, 
                       creationflags=creation_flags,
                       capture_output=True, # 捕获标准输出和标准错误
                       text=True # 以文本模式处理输出
                       )
        print(f"文件 '{os.path.basename(filepath)}' 已成功复制到剪贴板。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: PowerShell命令执行失败，无法复制文件到剪贴板。")
        print(f"命令: {e.cmd}")
        print(f"返回码: {e.returncode}")
        print(f"标准输出: {e.stdout}")
        print(f"标准错误: {e.stderr}")
        return False
    except FileNotFoundError:
        print("错误: 找不到'powershell'命令。请确保PowerShell已正确安装并添加到系统PATH中。")
        return False
    except Exception as e:
        print(f"错误: 复制文件到剪贴板时发生未知错误。详情: {e}")
        return False

def cleanup_powerpoint(app):
    """
    清理并关闭PowerPoint应用程序实例。

    __doc__:
        如果传入有效的PowerPoint应用程序COM对象，则尝试关闭它。
        此外，还会尝试解除COM对象的引用，以确保资源正确释放，
        防止PowerPoint进程残留。

    Args:
        app (win32com.client.Dispatch): PowerPoint应用程序COM对象。
    """
    if app:
        try:
            app.Quit()
            print("PowerPoint 应用程序已退出。")
        except Exception as e:
            print(f"警告: 关闭PowerPoint应用程序时发生错误。详情: {e}")
        finally:
            try:
                if hasattr(app, '_oleobj_'):
                    win32api.CoDisconnectObject(app._oleobj_) 
                del app
            except Exception as e:
                print(f"警告: 释放PowerPoint COM对象时发生错误。详情: {e}")

---

## 主程序流程

```python
def main_process(save_directory="D:\\", delay_seconds=5, 
                 powerpoint_visible=True, create_powerpoint_if_not_running=True,
                 require_active_presentation=True, filename_prefix=None,
                 timestamp_format="%Y%m%d_%H%M%S", file_extension=".pptx",
                 powerpoint_save_format=None, hide_powershell_window=True):
    """
    协调整个保存、复制和退出的主流程。

    __doc__:
        这是程序的入口点和主协调函数。
        它按顺序调用各个子函数来完成：
        1. 平台检测和Office版本检测。
        2. 获取PowerPoint应用程序实例。
        3. 获取当前活跃的演示文稿。
        4. 生成带时间戳的文件路径。
        5. 保存演示文稿。
        6. 将保存的文件复制到剪贴板。
        7. 延迟指定时间。
        8. 清理并关闭PowerPoint应用程序。
        在每个步骤中都包含错误检查，如果任何关键步骤失败，则提前终止。

    Args:
        save_directory (str): 文件保存的目标目录，默认为 "D:\\"。
        delay_seconds (int): 程序退出前的延迟秒数，默认为5秒。
        powerpoint_visible (bool): 控制PowerPoint应用程序是否可见，默认为True。
        create_powerpoint_if_not_running (bool): 如果PowerPoint未运行，是否启动新实例，默认为True。
        require_active_presentation (bool): 是否强制要求存在活跃的演示文稿，默认为True。
        filename_prefix (str, optional): 新文件名的前缀。如果为None，则使用原始演示文稿的文件名。
        timestamp_format (str): 时间戳的格式字符串，默认为 "%Y%m%d_%H%M%S"。
        file_extension (str): 保存文件的扩展名，默认为 ".pptx"。
        powerpoint_save_format (int, optional): PowerPoint文件保存格式的常量。例如，ppSaveAsOpenXMLPresentation (24)。
                                              如果为None，PowerPoint会根据文件扩展名自动选择。
        hide_powershell_window (bool): 是否隐藏PowerShell窗口，默认为True。
    """
    powerpoint_app = None # 初始化为None，确保在finally块中可以安全检查

    # 1. 平台检测
    if not check_platform():
        return # 如果不是Windows平台，直接退出

    # 2. Office 版本检测
    office_version = get_office_version()
    print(f"检测到的 Office PowerPoint 版本: {office_version}")
    
    try:
        # 3. 获取PowerPoint应用程序
        powerpoint_app = get_powerpoint_app(
            visible=powerpoint_visible,
            create_new_if_not_running=create_powerpoint_if_not_running
        )
        if not powerpoint_app:
            print("程序终止: 无法获取PowerPoint应用程序实例。")
            return

        # 4. 获取当前活跃的演示文稿
        current_presentation = get_active_presentation(
            powerpoint_app,
            require_active=require_active_presentation
        )
        if not current_presentation:
            print("程序终止: 未找到活跃的演示文稿。")
            return

        # 5. 生成带时间戳的文件路径
        new_filepath = generate_timestamped_filepath(
            current_presentation,
            directory=save_directory,
            filename_prefix=filename_prefix,
            timestamp_format=timestamp_format,
            file_extension=file_extension
        )
        if not new_filepath:
            print("程序终止: 无法生成有效的保存路径。")
            return

        # 6. 保存演示文稿
        if not save_presentation(
            current_presentation,
            new_filepath,
            file_format=powerpoint_save_format
        ):
            print("程序终止: 演示文稿保存失败。")
            return

        # 7. 复制文件到剪贴板
        if not copy_file_to_clipboard(
            new_filepath,
            hide_powershell_window=hide_powershell_window
        ):
            print("警告: 文件复制到剪贴板操作未能完全成功。")
            
        print(f"程序将在{delay_seconds}秒后退出...")
        time.sleep(delay_seconds)

    except Exception as e:
        print(f"主程序执行过程中发生意外错误: {e}")
    finally:
        # 8. 清理并关闭PowerPoint应用程序
        cleanup_powerpoint(powerpoint_app)
        
if __name__ == "__main__":
    # 示例用法：
    # 使用所有默认值
    # main_process() 

    # 示例用法：将文件保存到 E:\MyPPTs 目录，文件名以 "Report" 开头，不显示PowerPoint窗口
    # main_process(
    #     save_directory="E:\\MyPPTs",
    #     filename_prefix="Report",
    #     powerpoint_visible=False
    # )

    # 示例用法：将文件保存为 PDF 格式 (需要Office支持此导出功能)
    # 注意: PowerPoint的保存格式常量需要从 win32com.client.constants 中获取
    # 例如：win32com.client.constants.ppSaveAsPDF (32)
    # 确保在使用前导入 win32com.client.constants
    # from win32com.client import constants as pp_constants
    # main_process(
    #     file_extension=".pdf",
    #     powerpoint_save_format=pp_constants.ppSaveAsPDF
    # )
    
    main_process() # 运行主流程，所有参数使用默认值