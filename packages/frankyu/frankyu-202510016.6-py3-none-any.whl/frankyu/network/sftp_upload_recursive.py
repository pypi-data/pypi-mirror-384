import sys
import os
import datetime
import subprocess
from pathlib import Path
import time

# --- 配置区域 ---
REMOTE_HOST = "192.168.112.144"
REMOTE_PORT = 8022
REMOTE_USER = "u0_a454"

REMOTE_PATH_BASE = "/storage/emulated/0/Download/360a/"
TARGET_SUBDIR_MAIN = "FT1_UUID_0QA"
TARGET_SUBDIR_TEMP = "TEMP_FT1_0QA"
# --- 配置区域结束 ---

def get_current_formatted_datetime():
    """
    获取当前日期和时间，并格式化为 YYYYMMDD 和 HHMMSS_ms。
    """
    now = datetime.datetime.now()
    today_date_dir = now.strftime("%Y%m%d")  # YYYYMMDD 格式
    ms = now.strftime("%f")[:3]  # 获取微秒，取前三位作为毫秒
    timestamp_part = now.strftime(f"%Y%m%d_%H%M%S_{ms}")
    return today_date_dir, timestamp_part

def sftp_upload_recursive(): # 函数名已优化，体现递归上传
    if len(sys.argv) < 2:
        print("错误: 请提供至少一个本地源文件/目录路径或包含通配符的路径作为参数。")
        print(f"用法示例: python {Path(sys.argv[0]).name} \"C:\\path\\to\\file1.txt\" \"C:\\path\\to\\my_folder\" \"C:\\another\\directory\\*.log\"")
        sys.exit(1)

    input_paths = sys.argv[1:]

    today_date_dir, _ = get_current_formatted_datetime() 
    full_remote_path_main_date = Path(REMOTE_PATH_BASE) / TARGET_SUBDIR_MAIN / today_date_dir
    full_remote_path_temp_date = Path(REMOTE_PATH_BASE) / TARGET_SUBDIR_TEMP / today_date_dir

    # --- 尝试连接并创建远程目录 (基础日期目录) ---
    while True:
        print(f"\n正在尝试连接到 {REMOTE_HOST}:{REMOTE_PORT}...")
        try:
            subprocess.run(
                ["ssh", "-q", "-p", str(REMOTE_PORT), f"{REMOTE_USER}@{REMOTE_HOST}", "exit"],
                check=True,
                capture_output=True,
                text=True
            )
            print("连接成功！")
            break
        except subprocess.CalledProcessError as e:
            print(f"连接失败 ({e.stderr.strip() if e.stderr else e})，10秒后重试...")
            time.sleep(10)
        except FileNotFoundError:
            print("错误: 'ssh' 命令未找到。请确保 OpenSSH 客户端已安装并配置在系统路径中。")
            sys.exit(1)

    print("\n正在检查和创建远程目录...")
    remote_dirs_created = False
    for remote_dir_path in [full_remote_path_main_date, full_remote_path_temp_date]:
        print(f"检查/创建目录: {remote_dir_path}")
        try:
            subprocess.run(
                ["ssh", "-p", str(REMOTE_PORT), f"{REMOTE_USER}@{REMOTE_HOST}", f"mkdir -p '{remote_dir_path}'"],
                check=True,
                capture_output=True,
                text=True
            )
            remote_dirs_created = True
        except subprocess.CalledProcessError as e:
            print(f"创建目录失败 ({e.stderr.strip() if e.stderr else e})！请检查远程用户权限或路径设置。")
        except FileNotFoundError:
            print("错误: 'ssh' 命令未找到。请确保 OpenSSH 客户端已安装并配置在系统路径中。")
            sys.exit(1)

    if not remote_dirs_created:
        print("所有远程日期目录创建失败。请检查配置和权限。")
        sys.exit(1)
    print("远程日期目录已准备就绪。")

    # --- 收集所有要复制的实际文件/目录路径 ---
    items_to_copy = [] # 更改名称，因为可能包含文件和目录
    for input_path_str in input_paths:
        local_path_obj = Path(input_path_str).resolve()

        # 检查是否是递归通配符 (如 '**')
        if '**' in input_path_str:
            try:
                # 获取通配符的基础路径（如果用户输入的是相对路径，则从当前工作目录开始 glob）
                # 例如，如果输入是 "my_folder/**/*.txt"，则 glob 应该是 "my_folder/**/*.txt"
                # 如果输入是 "./**/*.txt"，则 glob 应该是 "**/*.txt"
                # Path.cwd().glob(input_path_str) 是一个更通用的处理方式
                for found_item in Path(os.getcwd()).glob(input_path_str):
                    if found_item.is_file(): # 递归通配符通常只用于查找文件
                        items_to_copy.append(found_item.resolve())
            except Exception as e:
                print(f"警告: 无法展开递归通配符路径 '{input_path_str}' - {e}")
        elif "*" in local_path_obj.name or "?" in local_path_obj.name: # 非递归通配符
            try:
                parent_dir = local_path_obj.parent
                for found_item in parent_dir.glob(local_path_obj.name):
                    if found_item.is_file():
                        items_to_copy.append(found_item)
            except Exception as e:
                print(f"警告: 无法展开通配符路径 '{input_path_str}' - {e}")
        elif local_path_obj.exists(): # 检查是否存在 (文件或目录)
            items_to_copy.append(local_path_obj)
        else:
            print(f"警告: 源路径 '{input_path_str}' 不存在，将跳过。")

    if not items_to_copy:
        print("没有找到任何要复制的有效文件或目录。")
        sys.exit(0)

    print(f"\n总共找到 {len(items_to_copy)} 个文件或目录待复制。")

    failed_uploads = [] 

    for i, local_source_item in enumerate(items_to_copy):
        item_type = "目录" if local_source_item.is_dir() else "文件"
        print(f"\n--- 正在复制 {item_type} {i+1}/{len(items_to_copy)}: {local_source_item.name} ---")

        copy_successful = False
        
        # 根据是文件还是目录来构建不同的 scp 命令
        if local_source_item.is_file():
            # 为文件生成时间戳文件名
            _, timestamp_for_filename = get_current_formatted_datetime()
            filename_no_ext = local_source_item.stem
            file_ext = local_source_item.suffix
            remote_final_name = f"{filename_no_ext}_{timestamp_for_filename}{file_ext}"
            
            # 远程目标路径包含文件名
            remote_target_main_path = full_remote_path_main_date / remote_final_name
            remote_target_temp_path = full_remote_path_temp_date / remote_final_name
            
            scp_command_base = ["scp", "-P", str(REMOTE_PORT)]
            print(f"目标文件（带时间戳）: {remote_final_name}")

        elif local_source_item.is_dir():
            # 为目录，远程目标路径不包含文件名，只指定父目录，scp -r 会创建同名子目录
            remote_final_name = local_source_item.name # 目录名保持不变
            
            # scp -r 将 source_dir 复制到 target_dir/source_dir
            # 所以远程目标是日期目录本身
            remote_target_main_path = full_remote_path_main_date
            remote_target_temp_path = full_remote_path_temp_date

            scp_command_base = ["scp", "-r", "-P", str(REMOTE_PORT)] # 添加 -r 选项
            print(f"目标目录: {remote_final_name} 将复制到 {remote_target_main_path}/")


        for attempt_idx in range(2): 
            target_remote_path = remote_target_main_path if attempt_idx == 0 else remote_target_temp_path
            
            if attempt_idx == 0:
                print(f"尝试复制到主目录: {target_remote_path}")
            else:
                print(f"主目录复制失败，尝试复制到备用目录: {target_remote_path}")

            try:
                full_scp_command = scp_command_base + [str(local_source_item), f"{REMOTE_USER}@{REMOTE_HOST}:{target_remote_path}"]
                subprocess.run(
                    full_scp_command,
                    check=True,
                    text=True
                )
                print(f"{item_type} '{local_source_item.name}' 成功复制到: {target_remote_path}/{' (包含子目录)' if local_source_item.is_dir() else remote_final_name}")
                copy_successful = True
                break
            except subprocess.CalledProcessError as e:
                print(f"复制失败 ({e.stderr.strip() if e.stderr else e})")
            except FileNotFoundError:
                print("错误: 'scp' 命令未找到。请确保 OpenSSH 客户端已安装并配置在系统路径中。")
                sys.exit(1)
        
        if not copy_successful:
            print(f"{item_type} '{local_source_item.name}' 复制失败，将跳过此项。")
            failed_uploads.append(f"{item_type}: {local_source_item.name}")
            time.sleep(2) 

    print("\n所有文件及目录复制任务完成。")

    if failed_uploads:
        print("\n--- 上传失败的项 ---")
        for item_info in failed_uploads:
            print(f"- {item_info}")
    else:
        print("\n所有文件及目录均成功上传。")

    input("按任意键继续 . . .")

if __name__ == "__main__":
    sftp_upload_recursive() # 调用新的函数名
