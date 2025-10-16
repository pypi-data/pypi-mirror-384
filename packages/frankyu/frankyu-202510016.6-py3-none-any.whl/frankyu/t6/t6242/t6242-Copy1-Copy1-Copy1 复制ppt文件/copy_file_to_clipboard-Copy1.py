import win32com.client
import datetime
import os
import time
import subprocess
import pythoncom # 用于释放COM对象

def get_powerpoint_app():
    """获取或启动PowerPoint应用程序实例。"""
    try:
        powerpoint_app = win32com.client.Dispatch("PowerPoint.Application")
        powerpoint_app.Visible = True # 确保PowerPoint是可见的
        print("已连接到PowerPoint应用程序。")
        return powerpoint_app
    except Exception as e:
        print(f"无法启动或连接到PowerPoint应用程序: {e}")
        return None

def get_active_presentation(app):
    """获取当前活跃的演示文稿。"""
    if not app:
        return None
    
    try:
        if app.Presentations.Count == 0:
            print("没有打开的演示文稿。请打开一个PowerPoint文件。")
            return None
        return app.ActivePresentation
    except Exception as e:
        print(f"获取当前活跃演示文稿时发生错误: {e}")
        return None

def generate_timestamped_filepath(presentation, directory="D:\\"):
    """
    生成带时间戳的文件保存路径。
    
    Args:
        presentation: PowerPoint演示文稿对象。
        directory (str): 文件保存的目标目录。
        
    Returns:
        str: 完整的文件保存路径，如果无法生成则返回None。
    """
    if not presentation:
        return None
        
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = os.path.splitext(os.path.basename(presentation.FullName))[0]
        new_filename = f"{original_filename}_{timestamp}.pptx"
        new_filepath = os.path.join(directory, new_filename)
        print(f"生成的目标文件路径: {new_filepath}")
        return new_filepath
    except Exception as e:
        print(f"生成文件路径时发生错误: {e}")
        return None

def save_presentation(presentation, filepath):
    """
    保存演示文稿到指定路径。
    
    Args:
        presentation: PowerPoint演示文稿对象。
        filepath (str): 文件的完整保存路径。
        
    Returns:
        bool: 如果保存成功则返回True，否则返回False。
    """
    if not presentation or not filepath:
        return False
        
    try:
        presentation.SaveAs(filepath)
        print(f"演示文稿已成功保存到: {filepath}")
        return True
    except Exception as e:
        print(f"保存演示文稿时发生错误: {e}")
        return False

def copy_file_to_clipboard(filepath):
    """
    将指定文件复制到剪贴板。
    使用PowerShell命令模拟Windows的文件复制操作。
    
    Args:
        filepath (str): 要复制的文件的完整路径。
        
    Returns:
        bool: 如果复制成功则返回True，否则返回False。
    """
    if not filepath or not os.path.exists(filepath):
        print(f"文件 '{filepath}' 不存在或路径无效，无法复制到剪贴板。")
        return False

    try:
        powershell_command = f'Set-Clipboard -LiteralPath "{filepath}"'
        # CREATE_NO_WINDOW 隐藏PowerShell窗口
        subprocess.run(["powershell", "-Command", powershell_command], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("文件已成功复制到剪贴板。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"PowerShell命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"复制文件到剪贴板时发生错误: {e}")
        return False

def cleanup_powerpoint(app):
    """
    清理并关闭PowerPoint应用程序实例。
    
    Args:
        app: PowerPoint应用程序对象。
    """
    if app:
        try:
            app.Quit()
            # 释放COM对象，防止资源泄露
            pythoncom.CoUninitialize() # 可能需要根据具体情况调整，通常在Dispatch后不需要手动CoUninitialize
            print("PowerPoint 应用程序已退出。")
        except Exception as e:
            print(f"关闭PowerPoint应用程序时发生错误: {e}")

def main_process():
    """协调整个保存、复制和退出的主流程。"""
    powerpoint_app = None # 初始化为None

    try:
        powerpoint_app = get_powerpoint_app()
        if not powerpoint_app:
            return

        current_presentation = get_active_presentation(powerpoint_app)
        if not current_presentation:
            return

        new_filepath = generate_timestamped_filepath(current_presentation, "D:\\")
        if not new_filepath:
            return

        if not save_presentation(current_presentation, new_filepath):
            return

        if not copy_file_to_clipboard(new_filepath):
            print("文件复制到剪贴板操作未能成功完成。")
            
        print("程序将在5秒后退出...")
        time.sleep(5)

    except Exception as e:
        print(f"主程序执行过程中发生意外错误: {e}")
    finally:
        cleanup_powerpoint(powerpoint_app)
        
if __name__ == "__main__":
    main_process()