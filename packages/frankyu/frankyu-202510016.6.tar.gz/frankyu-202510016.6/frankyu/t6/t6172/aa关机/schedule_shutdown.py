import os
import datetime
import sys
import time
import logging

# --- 配置日志系统 ---
# 日志记录器在函数外部定义，但其文件处理器会在每次调用函数时动态更新
# 以指向新的带时间戳的日志文件。

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 清除可能存在的旧处理器，确保每次只添加新的文件处理器
# 这样可以避免每次调用 schedule_shutdown 时都添加一个新的文件处理器，导致日志重复写入。
if logger.hasHandlers():
    logger.handlers.clear()

# -----------------------------------------------------------

def schedule_shutdown(
    delay_seconds: int = 36000,  # 关机延迟时间，单位秒。默认 36000 秒 (10 小时)
    prefer_custom_command: bool = True # 是否优先尝试使用 frankyu.cmd.command_execute
) -> bool:
    """
    安排系统关机，并记录关机详情及执行日志，支持跨平台，增加错误检测和处理。
    每次运行会在当前目录下指定的文件夹（例如 'shutdown_logs'）中，
    保存带时间戳的日志和信息文件。

    参数:
        delay_seconds (int): 关机前的延迟时间，单位秒。
                               默认为 36000 秒 (10 小时)。
        prefer_custom_command (bool): 如果为 True 且 frankyu 模块可用，则优先尝试使用
                                       frankyu.cmd.command_execute；如果 frankyu 失败，
                                       将回退到 os.system。如果为 False 或 frankyu 不可用，
                                       则直接使用 os.system。默认为 True。
    返回:
        bool: 如果命令成功执行（或被跳过），则返回 True；否则返回 False。
    """
    # 定义固定的根日志目录名
    log_base_dir = "shutdown_logs"
    
    # --- 生成唯一的文件时间戳 ---
    # 使用微秒确保时间戳的唯一性，避免在短时间内多次调用导致文件名冲突。
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    try:
        # 创建基础日志目录（如果不存在），exist_ok=True 避免目录已存在时抛出错误
        os.makedirs(log_base_dir, exist_ok=True)
        print(f"✅ 已确保日志目录存在: **{log_base_dir}**")
    except Exception as e:
        # 捕获创建目录时可能发生的任何错误，并打印和记录日志
        error_msg = f"❌ 错误: 无法创建日志目录 '{log_base_dir}': {e}"
        print(error_msg)
        logger.error(error_msg)
        return False

    # --- 配置本次运行的日志文件 ---
    # 每次函数调用都重新配置日志文件的输出路径
    for handler in logger.handlers[:]: # 遍历现有处理器副本，防止在循环中修改列表
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler) # 移除旧的文件处理器，确保日志只写入当前会话文件

    log_filename = os.path.join(log_base_dir, f"shutdown_script_{timestamp_str}.log")
    log_file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    log_file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file_handler.setFormatter(formatter)
    logger.addHandler(log_file_handler)

    logger.info(f"函数开始执行: delay={delay_seconds}s, prefer_custom={prefer_custom_command}. 日志保存至: {log_filename}")

    # --- 有条件地导入 frankyu.cmd.command_execute 模块 (在每次调用时重新检查) ---
    _has_custom_command_module = False
    cm = None # 初始化 cm 为 None
    try:
        # 尝试导入自定义命令执行模块
        import frankyu.cmd.command_execute as loaded_cm
        cm = loaded_cm
        _has_custom_command_module = True
        logger.info("已成功导入 frankyu.cmd.command_execute 模块。")
    except ImportError:
        # 如果模块不存在，记录警告
        logger.warning("无法导入 frankyu.cmd.command_execute 模块。将尝试使用 os.system。")
    except Exception as e:
        # 捕获导入时可能发生的其他未知错误
        logger.error(f"导入 frankyu.cmd.command_execute 模块时发生未知错误: {e}。将尝试使用 os.system。")


    # --- 1. 参数验证 ---
    try:
        # 尝试将 delay_seconds 转换为整数
        delay_seconds = int(delay_seconds)
        if delay_seconds < 0:
            # 如果延迟时间为负数，则抛出错误
            error_msg = f"错误: 延迟时间 (delay_seconds) 不能为负数。收到: {delay_seconds}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            return False
    except ValueError:
        # 如果 delay_seconds 无法转换为整数，则抛出错误
        error_msg = f"错误: 延迟时间 (delay_seconds) 必须是有效的整数。收到: {delay_seconds}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False
    
    # 定义本次运行的 shutdown_info 文件名
    output_filename_with_timestamp = os.path.join(log_base_dir, f"shutdown_info_{timestamp_str}.txt")


    # 根据操作系统设置命令和命令连接符
    shutdown_command_prefix = "" # 关机命令前缀
    abort_command = ""           # 取消关机命令
    ping_command = ""            # 用于命令之间短暂延迟的ping命令
    command_separator = ""       # 命令连接符
    full_shutdown_command = ""   # 完整的关机命令
    
    if sys.platform.startswith('win'):
        # Windows 系统命令
        shutdown_command_prefix = "shutdown -s -t" # -s 表示关机，-t 表示延迟时间
        abort_command = "shutdown -a" # -a 表示取消关机
        ping_command = "ping 127.0.0.1 -n 1" # ping 本地回环地址1次，用于确保前一个命令执行完毕
        command_separator = "&" # Windows 命令连接符
        full_shutdown_command = (
            f"{abort_command} {command_separator} " # 先尝试取消之前的关机计划
            f"{ping_command} {command_separator} "   # 短暂延迟
            f"{shutdown_command_prefix} {delay_seconds}" # 设置新的关机计划
        )
    elif sys.platform.startswith('darwin'):
        # macOS 系统命令
        # macOS 取消关机没有直接的命令，通常需要手动干预或杀死进程
        abort_command = (
            "echo '在macOS上取消已计划的关机可能需要手动干预，"
            "例如杀死相关的shutdown进程。'"
        )
        shutdown_command_prefix = "sudo shutdown -h +" # macOS 关机命令，-h 表示关机，+ 表示延迟分钟数
        ping_command = "ping -c 1 127.0.0.1" # ping 本地回环地址1次
        command_separator = ";" # Unix/Linux 命令连接符
        
        # macOS 和 Linux 的 shutdown 命令接受分钟数，所以需要将秒转换为分钟并向上取整
        delay_minutes = max(1, (delay_seconds + 59) // 60) # 向上取整，至少1分钟
        full_shutdown_command = (
            f"{abort_command} {command_separator} " # 先执行取消命令（通常是提示信息）
            f"{ping_command} {command_separator} "   # 短暂延迟
            f"{shutdown_command_prefix}{delay_minutes}" # 设置新的关机计划
        )
        print("注意：在 macOS 上执行 'sudo shutdown' 通常需要管理员密码。")
        print("如果没有配置无密码sudo，请准备输入密码。")
        print("如果您不想输入密码，并且在GUI环境下，")
        print("可以尝试使用 'osascript -e 'tell app \"System Events\" to shut down'' 来替代关机命令。")
        logger.warning("在 macOS 上，'sudo shutdown' 可能需要管理员密码。")
        logger.warning("考虑在 GUI 环境下使用 'osascript'。")
    else: # Linux 或其他类 Unix 系统
        # Linux 系统命令 (与 macOS 类似)
        shutdown_command_prefix = "sudo shutdown -h +" # Linux 关机命令
        abort_command = "sudo shutdown -c" # Linux 的取消关机命令
        ping_command = "ping -c 1 127.0.0.1" # ping 本地回环地址1次
        command_separator = ";" # Unix/Linux 命令连接符

        delay_minutes = max(1, (delay_seconds + 59) // 60) # 向上取整，至少1分钟
        full_shutdown_command = (
            f"{abort_command} {command_separator} " # 先取消之前的关机计划
            f"{ping_command} {command_separator} "   # 短暂延迟
            f"{shutdown_command_prefix}{delay_minutes}" # 设置新的关机计划
        )
        print("注意：在 Linux 上执行 'sudo shutdown' 通常需要管理员密码。")
        print("如果没有配置无密码sudo，请准备输入密码。")
        logger.warning("在 Linux 上，'sudo shutdown' 可能需要管理员密码。")
        logger.warning("如果无人值守运行，请确保 sudoers 已配置。")

    logger.info(f"检测到操作系统: {sys.platform}。构建的命令: {full_shutdown_command}")


    # 获取当前时间并计算结束时间
    now = datetime.datetime.now()
    endtime = now + datetime.timedelta(seconds=delay_seconds)

    # 准备要写入文件和打印的文本，详细列出关机计划信息
    output_text = (
        f'''--- 关机计划详情 ---\n\n'''
        f'''开机时间: {now.strftime("%Y-%m-%d %H:%M:%S")}\n'''
        f'''间隔时间: {datetime.timedelta(seconds=delay_seconds)} ({delay_seconds} 秒)\n'''
        f'''预计关机时间: {endtime.strftime("%Y-%m-%d %H:%M:%S")}\n'''
        f'''操作系统: {sys.platform}\n'''
        f'''将要执行的命令: {full_shutdown_command}\n\n'''
        f'''--------------------'''
    )


    # --- 2. 文件操作错误处理 ---
    try:
        # 将关机信息写入文件
        with open(output_filename_with_timestamp, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"✅ 关机信息已成功保存到 **{output_filename_with_timestamp}**")
        logger.info(f"关机信息概要已成功保存到 {output_filename_with_timestamp}")
    except PermissionError:
        # 捕获权限错误
        error_msg = f"错误: 没有权限写入文件 {output_filename_with_timestamp}。"
        error_msg += "请检查文件权限或选择其他路径。"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False
    except IOError as e:
        # 捕获一般的I/O错误
        error_msg = f"写入文件 {output_filename_with_timestamp} 时发生 I/O 错误: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False
    except Exception as e:
        # 捕获所有其他未知错误
        error_msg = f"写入文件 {output_filename_with_timestamp} 时发生未知错误: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False

    # 将信息打印到控制台
    print(output_text)


    # --- 3. 命令执行逻辑 (优先 frankyu.cmd.command_execute，失败则回退到 os.system) ---
    command_executed_successfully = False

    # 如果优先使用自定义命令且模块已成功导入
    if prefer_custom_command and _has_custom_command_module:
        print(f"\n--- 尝试通过 frankyu.cmd.command_execute 执行命令 (优先模式) ---")
        logger.info(f"尝试通过 frankyu.cmd.command_execute 执行命令: {full_shutdown_command}")
        try:
            # 调用自定义模块的命令执行函数
            cm.execute_command(full_shutdown_command)
            print(f"✅ frankyu.cmd.command_execute 命令执行成功。")
            logger.info("frankyu.cmd.command_execute 命令执行成功。")
            command_executed_successfully = True
        except PermissionError:
            # 自定义命令执行时权限不足，尝试回退
            error_msg = "通过 frankyu.cmd.command_execute 执行时权限不足。"
            error_msg += "将尝试回退到 os.system。"
            print(f"❌ {error_msg}")
            logger.warning(error_msg)
        except Exception as e:
            # 自定义命令执行时发生其他异常，尝试回退
            error_msg = f"通过 frankyu.cmd.command_execute 执行命令时发生异常: {e}。"
            error_msg += "将尝试回退到 os.system。"
            print(f"❌ {error_msg}")
            logger.warning(error_msg)
    elif prefer_custom_command and not _has_custom_command_module:
        # 优先使用自定义命令但模块未导入
        print("\n--- 无法使用 frankyu.cmd.command_execute (模块未导入)。将直接使用 os.system。---")
        logger.info("frankyu.cmd.command_execute 模块不可用。回退到 os.system。")
    else: # prefer_custom_command 为 False
        # 不优先使用自定义命令，直接使用 os.system
        print("\n--- 未优先使用 frankyu.cmd.command_execute。将直接使用 os.system。---")
        logger.info("未优先使用自定义命令。直接使用 os.system。")


    # 如果自定义命令未被优先使用，或其执行失败/不可用，则回退到 os.system
    if not command_executed_successfully:
        print(f"\n--- 尝试通过 os.system 执行命令 ---")
        logger.info(f"尝试通过 os.system 执行命令: {full_shutdown_command}")
        try:
            # 使用 os.system 执行命令
            result_code = os.system(full_shutdown_command)
            
            if result_code != 0:
                # 如果返回码不为0，表示命令执行失败
                error_msg = f"os.system 命令执行失败。退出码: {result_code}"
                print(f"❌ {error_msg}")
                logger.error(error_msg)
                if sys.platform.startswith('darwin') or sys.platform.startswith('linux'):
                    # 对于macOS和Linux，通常是权限问题
                    print("提示: 这可能是由于缺乏 'sudo' 权限或需要输入密码。")
                    print("请确保您有必要的权限。")
                    logger.warning("潜在的权限问题或 sudo 命令需要密码。")
                command_executed_successfully = False
            else:
                # 命令执行成功
                print(f"✅ os.system 命令执行成功。")
                logger.info("os.system 命令执行成功。")
                command_executed_successfully = True
        except Exception as e:
            # 捕获 os.system 执行时可能发生的异常
            error_msg = f"通过 os.system 执行命令时发生异常: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            command_executed_successfully = False

    if not command_executed_successfully:
        # 如果最终命令未能成功执行，打印警告信息
        final_status_msg = "关机命令未能成功执行。请检查上述错误信息。"
        print(f"\n🚫 警告: **{final_status_msg}**")
        logger.error(f"最终状态: {final_status_msg}")
        return False
    else:
        # 命令成功发送，打印成功信息
        final_status_msg = "关机命令已成功发送。"
        print(f"\n🎉 成功: **{final_status_msg}**")
        logger.info(f"最终状态: {final_status_msg}")
        return True


# -----------------------------------------------------------

## 脚本主入口点

if __name__ == "__main__":
    # 这是脚本的入口点，当直接运行这个脚本时，这里的代码会被执行。
    print("--- 脚本开始执行 ---")
    
    # 示例1: 默认关机，延迟 10 小时 (36000 秒)，优先使用自定义命令 (如果可用)
    # schedule_shutdown()
    
    # 示例2: 延迟 60 秒关机，不优先使用自定义命令 (直接使用 os.system)
    # schedule_shutdown(delay_seconds=60, prefer_custom_command=False)

    # 示例3: 延迟 10 分钟 (600 秒) 关机，优先使用自定义命令
    # 你可以根据需要调整 delay_seconds 的值，例如设置为 300 表示 5 分钟
    schedule_shutdown(delay_seconds=600, prefer_custom_command=True)

    print("\n--- 脚本执行结束 ---")