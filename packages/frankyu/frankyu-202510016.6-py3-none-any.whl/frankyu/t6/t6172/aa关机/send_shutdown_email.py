import os
import datetime
import sys
import time
import logging
import smtplib   #123123
from email.mime.text import MIMEText#123123
from email.mime.multipart import MIMEMultipart#123123

# --- 配置日志系统 ---
# 日志记录器在函数外部定义，但其文件处理器会在每次调用函数时动态更新
# 以指向新的带时间戳的日志文件。

logger = logging.getLogger(__name__)#123123
logger.setLevel(logging.INFO)#123123

# 清除可能存在的旧处理器，确保每次只添加新的文件处理器
if logger.hasHandlers():#123123
    logger.handlers.clear()#123123

# -----------------------------------------------------------


def send_shutdown_email(
    sender_email: str="yurx17@qq.com" ,
    sender_password: str="tltpcwaacooocffe",
    receiver_email: str="frank_yu@prime3c.com",
    subject: str="123",
    body: str="345",
    attachment_path: str = None # 日志文件的路径作为附件
):
    """
    发送邮件报告。根据发件人邮箱的域名自动选择SMTP服务器和端口。
    """
    if not sender_email or not sender_password or not receiver_email:
        print("❌ 错误: 邮件发送所需的发件人邮箱、密码或收件人邮箱未提供。跳过邮件发送。")
        logger.error("邮件发送所需的发件人邮箱、密码或收件人邮箱未提供。跳过邮件发送。")
        return

    # --- 自动配置 SMTP 服务器和端口 ---
    smtp_server = None
    smtp_port = None
    use_ssl = False # 标识是否使用 smtplib.SMTP_SSL
    
    email_domain = sender_email.split('@')[-1].lower() # 提取邮箱域名并转为小写

    if "qq.com" in email_domain:
        smtp_server = "smtp.qq.com"
        smtp_port = 465
        smtp_port = 587
        use_ssl = True
        use_ssl = 0
        logger.info(f"检测到 QQ 邮箱，使用配置: {smtp_server}:{smtp_port} (SSL)")
    elif "gmail.com" in email_domain:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        use_ssl = False # STARTTLS
        logger.info(f"检测到 Gmail 邮箱，使用配置: {smtp_server}:{smtp_port} (STARTTLS)")
    elif "163.com" in email_domain:
        smtp_server = "smtp.163.com"
        smtp_port = 465 # 163也支持587+STARTTLS
        use_ssl = True
        logger.info(f"检测到 163 邮箱，使用配置: {smtp_server}:{smtp_port} (SSL)")
    elif "outlook.com" in email_domain or "hotmail.com" in email_domain:
        smtp_server = "smtp.office365.com" # Outlook/Hotmail 通常使用这个服务器
        smtp_port = 587
        use_ssl = False # STARTTLS
        logger.info(f"检测到 Outlook/Hotmail 邮箱，使用配置: {smtp_server}:{smtp_port} (STARTTLS)")
    else:
        # 如果是未知邮箱，打印警告并使用通用配置或默认配置（可能需要手动指定）
        print(f"⚠️ 警告: 未识别的发件人邮箱域名 '{email_domain}'。将尝试通用 SMTP 配置 (smtp.yourdomain.com:587)。")
        logger.warning(f"未识别的发件人邮箱域名 '{email_domain}'。将尝试通用 SMTP 配置。")
        # 尝试一个通用配置，用户可能需要根据自己的域名调整
        smtp_server = f"smtp.{email_domain}"
        smtp_port = 587
        use_ssl = False

    if not smtp_server or not smtp_port:
        print("❌ 错误: 无法确定邮件服务器配置。请手动指定或检查发件人邮箱域名。")
        logger.error("无法确定邮件服务器配置。请手动指定或检查发件人邮箱域名。")
        return

    msg = MIMEMultipart() #123123
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8')) # 主体内容 #123123

    # 添加附件
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as f:
                # 对于日志文件，通常是文本，MIMEText是可行的。
                attach = MIMEText(f.read(), 'base64', 'utf-8')#123123
                #123123
                attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                #123123
                msg.attach(attach)
            logger.info(f"成功将日志文件 {attachment_path} 作为附件添加到邮件。")
        except Exception as e: #123123
            print(f"❌ 警告: 无法将附件 {attachment_path} 添加到邮件: {e}")
            logger.warning(f"无法将附件 {attachment_path} 添加到邮件: {e}")
    else:
        if attachment_path: # 如果提供了路径但文件不存在  #123123
            print(f"❌ 警告: 附件文件 {attachment_path} 不存在或路径无效。邮件将不包含此附件。")
            logger.warning(f"附件文件 {attachment_path} 不存在或路径无效。邮件将不包含此附件。")

    try:
        if use_ssl:  #123123
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)#123123
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)#123123
            server.starttls() # 启用 TLS 加密#123123

        server.login(sender_email, sender_password) # 使用授权码或密码登录#123123
        text = msg.as_string()#123123
        server.sendmail(sender_email, receiver_email, text)#123123
        server.quit()#123123
        print(f"✅ 邮件报告已成功发送至: **{receiver_email}**")
        logger.info(f"邮件报告已成功发送至: {receiver_email}")
    except smtplib.SMTPAuthenticationError:#123123
        print("❌ 错误: 邮件身份验证失败。请检查邮箱账号和**授权码/密码**是否正确，并确保已开启SMTP服务。")
        logger.error("邮件身份验证失败。请检查邮箱账号和**授权码/密码**是否正确，并确保已开启SMTP服务。")
    except smtplib.SMTPConnectError as e:
        print(f"❌ 错误: 无法连接到SMTP服务器 '{smtp_server}:{smtp_port}'。请检查SMTP服务器地址和端口，以及网络连接和防火墙。错误: {e}")
        logger.error(f"无法连接到SMTP服务器 '{smtp_server}:{smtp_port}'。请检查SMTP服务器地址和端口，以及网络连接和防火墙。错误: {e}")
    except Exception as e:
        print(f"❌ 邮件发送过程中发生未知错误: {e}")
        logger.error(f"邮件发送过程中发生未知错误: {e}")




def schedule_shutdown(
    delay_seconds: int = 36000,  # 关机延迟时间，单位秒。默认 36000 秒 (10 小时)
    prefer_custom_command: bool = True, # 是否优先尝试使用 frankyu.cmd.command_execute
    send_email_report: bool = False, # 是否发送邮件报告
    email_account: str = "yurx17@qq.com",         # 发件人邮箱账号
    email_password: str = "tltpcwaacooocffe",        # 发件人邮箱密码（或授权码）
    recipient_email: str = "frank_yu@prime3c.com"        # 收件人邮箱地址
) -> bool: #123123
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
        send_email_report (bool): 是否在函数执行完毕后发送邮件报告。
        email_account (str): 发送邮件的邮箱账号。当 send_email_report 为 True 时必需。
        email_password (str): 发送邮件的邮箱密码或授权码。当 send_email_report 为 True 时必需。
        recipient_email (str): 接收报告的邮箱地址。当 send_email_report 为 True 时必需。
    返回:
        bool: 如果命令成功执行（或被跳过），则返回 True；否则返回 False。
    """
    # 定义固定的根日志目录名
    log_base_dir = "shutdown_logs" 
    
    # --- 生成唯一的文件时间戳 ---
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    try:
        # 创建基础日志目录（如果不存在），exist_ok=True 避免目录已存在时抛出错误
        os.makedirs(log_base_dir, exist_ok=True)
        print(f"✅ 已确保日志目录存在: **{log_base_dir}**")
    except Exception as e: #123123
        # 捕获创建目录时可能发生的任何错误，并打印和记录日志
        error_msg = f"❌ 错误: 无法创建日志目录 '{log_base_dir}': {e}"
        print(error_msg)
        logger.error(error_msg)#123123
        return False

    # --- 配置本次运行的日志文件 ---
    # 每次函数调用都重新配置日志文件的输出路径
    for handler in logger.handlers[:]: # 遍历现有处理器副本，防止在循环中修改列表#123123
        if isinstance(handler, logging.FileHandler):#123123
            logger.removeHandler(handler) # 移除旧的文件处理器，确保日志只写入当前会话文件 #123123

    log_filename = os.path.join(log_base_dir, f"shutdown_script_{timestamp_str}.log")
    log_file_handler = logging.FileHandler(log_filename, encoding="utf-8")#123123
    log_file_handler.setLevel(logging.INFO)#123123
    #123123
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    #123123
    log_file_handler.setFormatter(formatter)#123123
    logger.addHandler(log_file_handler)#123123

    logger.info(f"函数开始执行: delay={delay_seconds}s, prefer_custom={prefer_custom_command}. 日志保存至: {log_filename}")
#123123
    # --- 有条件地导入 frankyu.cmd.command_execute 模块 (在每次调用时重新检查) ---
    _has_custom_command_module = False 
    cm = None # 初始化 cm 为 None  #123123
    try:
        # 尝试导入自定义命令执行模块
        import frankyu.cmd.command_execute as loaded_cm
        cm = loaded_cm
        _has_custom_command_module = True
        logger.info("已成功导入 frankyu.cmd.command_execute 模块。")#123123
    except ImportError:#123123
        # 如果模块不存在，记录警告
        #123123
        logger.warning("无法导入 frankyu.cmd.command_execute 模块。将尝试使用 os.system。")
    except Exception as e:#123123
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
            logger.error(error_msg)#123123
            # 如果需要发送邮件，则在这里发送错误报告
            if send_email_report:
                send_shutdown_email(email_account, email_password, recipient_email, "关机计划失败 - 参数错误", error_msg, None)
            return False
    except ValueError:#123123
        # 如果 delay_seconds 无法转换为整数，则抛出错误
        error_msg = f"错误: 延迟时间 (delay_seconds) 必须是有效的整数。收到: {delay_seconds}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        if send_email_report:
            send_shutdown_email(email_account, email_password, recipient_email, "关机计划失败 - 参数错误", error_msg, None)
        return False
    
    # 定义本次运行的 shutdown_info 文件名
    output_filename_with_timestamp = os.path.join(log_base_dir, f"shutdown_info_{timestamp_str}.txt")


    # 根据操作系统设置命令和命令连接符
    shutdown_command_prefix = "" # 关机命令前缀 
    abort_command = ""           # 取消关机命令
    ping_command = ""            # 用于命令之间短暂延迟的ping命令
    command_separator = ""       # 命令连接符
    full_shutdown_command = ""   # 完整的关机命令
    
    if sys.platform.startswith('win'):#123123
        # Windows 系统命令
        shutdown_command_prefix = "shutdown -s -t" # -s 表示关机，-t 表示延迟时间
        abort_command = "shutdown -a" # -a 表示取消关机
        #123123
        ping_command = "ping 127.0.0.1 -n 1" # ping 本地回环地址1次，用于确保前一个命令执行完毕
        command_separator = "&" # Windows 命令连接符  #123123
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
        shutdown_command_prefix = "sudo shutdown -h +" # Linux 关机命令#123123
        abort_command = "sudo shutdown -c" # Linux 的取消关机命令#123123
        ping_command = "ping -c 1 127.0.0.1" # ping 本地回环地址1次#123123
        command_separator = ";" # Unix/Linux 命令连接符#123123
        
#123123
        delay_minutes = max(1, (delay_seconds + 59) // 60) # 向上取整，至少1分钟
        full_shutdown_command = (
            f"{abort_command} {command_separator} " # 先取消之前的关机计划
            f"{ping_command} {command_separator} "   # 短暂延迟
            f"{shutdown_command_prefix}{delay_minutes}" # 设置新的关机计划
        )
        print("注意：在 Linux 上执行 'sudo shutdown' 通常需要管理员密码。")
        print("如果没有配置无密码sudo，请准备输入密码。")
        logger.warning("在 Linux 上，'sudo shutdown' 可能需要管理员密码。")
        logger.warning("如果无人值守运行，请确保 sudoers 已配置。")  #123123
#123123
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
    except PermissionError:#123123
        # 捕获权限错误
        error_msg = f"错误: 没有权限写入文件 {output_filename_with_timestamp}。"
        error_msg += "请检查文件权限或选择其他路径。"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        if send_email_report:
            send_shutdown_email(email_account, email_password, recipient_email, "关机计划失败 - 文件权限错误", error_msg, log_filename)#123123
        return False
    except IOError as e:  #123123
        # 捕获一般的I/O错误
        error_msg = f"写入文件 {output_filename_with_timestamp} 时发生 I/O 错误: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        if send_email_report:
            send_shutdown_email(email_account, email_password, recipient_email, "关机计划失败 - 文件写入错误", error_msg, log_filename)#123123
        return False
    except Exception as e:
        # 捕获所有其他未知错误
        error_msg = f"写入文件 {output_filename_with_timestamp} 时发生未知错误: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        if send_email_report:
            send_shutdown_email(email_account, email_password, recipient_email, "关机计划失败 - 未知文件错误", error_msg, log_filename)#123123
        return False

    # 将信息打印到控制台
    print(output_text)


    # --- 3. 命令执行逻辑 (优先 frankyu.cmd.command_execute，失败则回退到 os.system) ---
    command_executed_successfully = False
    execution_detail = "" # 用于记录命令执行的结果或错误信息

    if prefer_custom_command and _has_custom_command_module:
        print(f"\n--- 尝试通过 frankyu.cmd.command_execute 执行命令 (优先模式) ---")
        logger.info(f"尝试通过 frankyu.cmd.command_execute 执行命令: {full_shutdown_command}")
        try:
            # 调用自定义模块的命令执行函数
            cm.execute_command(full_shutdown_command)
            execution_detail = "frankyu.cmd.command_execute 命令执行成功。"
            print(f"✅ {execution_detail}")
            logger.info(execution_detail)#123123
            command_executed_successfully = True
        except PermissionError:#123123
            # 自定义命令执行时权限不足，尝试回退
            execution_detail = "通过 frankyu.cmd.command_execute 执行时权限不足。将尝试回退到 os.system。"
            print(f"❌ {execution_detail}")
            logger.warning(execution_detail)
        except Exception as e:
            # 自定义命令执行时发生其他异常，尝试回退
            execution_detail = f"通过 frankyu.cmd.command_execute 执行命令时发生异常: {e}。"
            error_msg = f"通过 frankyu.cmd.command_execute 执行命令时发生异常: {e}。"
            print(f"❌ {execution_detail}")
            logger.warning(execution_detail)#123123
    elif prefer_custom_command and not _has_custom_command_module:
        # 优先使用自定义命令但模块未导入
        execution_detail = "无法使用 frankyu.cmd.command_execute (模块未导入)。将直接使用 os.system。"
        print(f"\n--- {execution_detail} ---")
        logger.info(execution_detail)
    else: # prefer_custom_command 为 False
        # 不优先使用自定义命令，直接使用 os.system
        execution_detail = "未优先使用自定义命令。直接使用 os.system。"
        print(f"\n--- {execution_detail} ---")
        logger.info(execution_detail)


    # 如果自定义命令未被优先使用，或其执行失败/不可用，则回退到 os.system
    if not command_executed_successfully:
        print(f"\n--- 尝试通过 os.system 执行命令 ---")
        logger.info(f"尝试通过 os.system 执行命令: {full_shutdown_command}")
        try:
            # 使用 os.system 执行命令
            result_code = os.system(full_shutdown_command)
            
            if result_code != 0:#123123
                # 如果返回码不为0，表示命令执行失败
                execution_detail = f"os.system 命令执行失败。退出码: {result_code}"
                print(f"❌ {execution_detail}")
                logger.error(execution_detail)
                if sys.platform.startswith('darwin') or sys.platform.startswith('linux'):
                    # 对于macOS和Linux，通常是权限问题
                    print("提示: 这可能是由于缺乏 'sudo' 权限或需要输入密码。")
                    print("请确保您有必要的权限。")
                    logger.warning("潜在的权限问题或 sudo 命令需要密码。")
                command_executed_successfully = False
            else:
                # 命令执行成功
                execution_detail = "os.system 命令执行成功。"
                print(f"✅ {execution_detail}")
                logger.info(execution_detail)
                command_executed_successfully = True
        except Exception as e:
            # 捕获 os.system 执行时可能发生的异常
            execution_detail = f"通过 os.system 执行命令时发生异常: {e}"
            print(f"❌ {execution_detail}")
            logger.error(execution_detail)
            command_executed_successfully = False

    final_status_msg = ""  #123123
    if not command_executed_successfully: #123123
        final_status_msg = "关机命令未能成功执行。请检查上述错误信息。"
        print(f"\n🚫 警告: **{final_status_msg}**")
        logger.error(f"最终状态: {final_status_msg}")
        # 如果需要发送邮件，且之前没有因为参数或文件错误而退出，则在这里发送失败报告
        if send_email_report:  #123123
            send_shutdown_email(email_account, email_password, recipient_email, "关机计划失败", final_status_msg + "\n" + execution_detail, log_filename)
        return False
    else:
        final_status_msg = "关机命令已成功发送。"
        print(f"\n🎉 成功: **{final_status_msg}**")
        logger.info(f"最终状态: {final_status_msg}")
        # 如果需要发送邮件，且命令执行成功，则在这里发送成功报告
        if send_email_report:
            send_shutdown_email(email_account, email_password, recipient_email, "关机计划成功", final_status_msg + "\n" + output_text, log_filename)
        return True

# --- 邮件发送辅助函数 ---
def send_shutdown_email(
    sender_email: str,
    sender_password: str,
    receiver_email: str,
    subject: str,
    body: str,
    attachment_path: str = None # 日志文件的路径作为附件
):
    """
    发送邮件报告。根据发件人邮箱的域名自动选择SMTP服务器和端口。
    """
    if not sender_email or not sender_password or not receiver_email:
        print("❌ 错误: 邮件发送所需的发件人邮箱、密码或收件人邮箱未提供。跳过邮件发送。")
        logger.error("邮件发送所需的发件人邮箱、密码或收件人邮箱未提供。跳过邮件发送。")
        return

    # --- 自动配置 SMTP 服务器和端口 ---
    smtp_server = None
    smtp_port = None
    use_ssl = False # 标识是否使用 smtplib.SMTP_SSL
    
    email_domain = sender_email.split('@')[-1].lower() # 提取邮箱域名并转为小写

    if "qq.com" in email_domain:
        smtp_server = "smtp.qq.com"
        smtp_port = 587
        use_ssl = 0
        logger.info(f"检测到 QQ 邮箱，使用配置: {smtp_server}:{smtp_port} (SSL)")
    elif "gmail.com" in email_domain:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        use_ssl = False # STARTTLS
        logger.info(f"检测到 Gmail 邮箱，使用配置: {smtp_server}:{smtp_port} (STARTTLS)")
    elif "163.com" in email_domain:
        smtp_server = "smtp.163.com"
        smtp_port = 465 # 163也支持587+STARTTLS
        use_ssl = True
        logger.info(f"检测到 163 邮箱，使用配置: {smtp_server}:{smtp_port} (SSL)")
    elif "outlook.com" in email_domain or "hotmail.com" in email_domain:
        smtp_server = "smtp.office365.com" # Outlook/Hotmail 通常使用这个服务器
        smtp_port = 587
        use_ssl = False # STARTTLS
        logger.info(f"检测到 Outlook/Hotmail 邮箱，使用配置: {smtp_server}:{smtp_port} (STARTTLS)")
    else:
        # 如果是未知邮箱，打印警告并使用通用配置或默认配置（可能需要手动指定）
        print(f"⚠️ 警告: 未识别的发件人邮箱域名 '{email_domain}'。将尝试通用 SMTP 配置 (smtp.yourdomain.com:587)。")
        logger.warning(f"未识别的发件人邮箱域名 '{email_domain}'。将尝试通用 SMTP 配置。")
        # 尝试一个通用配置，用户可能需要根据自己的域名调整
        smtp_server = f"smtp.{email_domain}"
        smtp_port = 587
        use_ssl = False

    if not smtp_server or not smtp_port:
        print("❌ 错误: 无法确定邮件服务器配置。请手动指定或检查发件人邮箱域名。")
        logger.error("无法确定邮件服务器配置。请手动指定或检查发件人邮箱域名。")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8')) # 主体内容

    # 添加附件
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as f:
                # 对于日志文件，通常是文本，MIMEText是可行的。
                attach = MIMEText(f.read(), 'base64', 'utf-8')
                attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                msg.attach(attach)
            logger.info(f"成功将日志文件 {attachment_path} 作为附件添加到邮件。")
        except Exception as e:
            print(f"❌ 警告: 无法将附件 {attachment_path} 添加到邮件: {e}")
            logger.warning(f"无法将附件 {attachment_path} 添加到邮件: {e}")
    else:
        if attachment_path: # 如果提供了路径但文件不存在
            print(f"❌ 警告: 附件文件 {attachment_path} 不存在或路径无效。邮件将不包含此附件。")
            logger.warning(f"附件文件 {attachment_path} 不存在或路径无效。邮件将不包含此附件。")

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls() # 启用 TLS 加密

        server.login(sender_email, sender_password) # 使用授权码或密码登录
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print(f"✅ 邮件报告已成功发送至: **{receiver_email}**")
        logger.info(f"邮件报告已成功发送至: {receiver_email}")
    except smtplib.SMTPAuthenticationError:
        print("❌ 错误: 邮件身份验证失败。请检查邮箱账号和**授权码/密码**是否正确，并确保已开启SMTP服务。")
        logger.error("邮件身份验证失败。请检查邮箱账号和**授权码/密码**是否正确，并确保已开启SMTP服务。")
    except smtplib.SMTPConnectError as e:
        print(f"❌ 错误: 无法连接到SMTP服务器 '{smtp_server}:{smtp_port}'。请检查SMTP服务器地址和端口，以及网络连接和防火墙。错误: {e}")
        logger.error(f"无法连接到SMTP服务器 '{smtp_server}:{smtp_port}'。请检查SMTP服务器地址和端口，以及网络连接和防火墙。错误: {e}")
    except Exception as e:
        print(f"❌ 邮件发送过程中发生未知错误: {e}")
        logger.error(f"邮件发送过程中发生未知错误: {e}")

# -----------------------------------------------------------

## 脚本主入口点

if __name__ == "__main__":
    # 这是脚本的入口点，当直接运行这个脚本时，这里的代码会被执行。
    print("--- 脚本开始执行 ---")
    
    # --- 邮件配置示例 ---
    # 请将以下占位符替换为你的实际邮箱信息。
    # SENDER_PASSWORD 必须是授权码（对于QQ、Gmail、163等），而不是登录密码。
    # 
    # !!! 警告：请勿将你的真实密码（包括授权码）直接提交到公共代码库中 !!!
    # 在生产环境中，强烈建议使用环境变量或配置文件来管理敏感信息。
    
    SENDER_EMAIL = "yurx17@qq.com"  # 你的发件箱地址
    SENDER_PASSWORD = "tltpcwaacooocffe" # 你的邮箱密码或授权码
    RECEIVER_EMAIL = "frank_yu@prime3c.com" # 接收报告的邮箱地址

    # 示例：Gmail 邮箱配置 (需要开启两步验证并生成应用专用密码)
    # SENDER_EMAIL = "你的Gmail邮箱@gmail.com"
    # SENDER_PASSWORD = "你的Gmail应用专用密码"
    # RECEIVER_EMAIL = "收件人邮箱@example.com"

    # 示例：163 邮箱配置 (需要开启SMTP服务并获取授权码)
    # SENDER_EMAIL = "你的163邮箱@163.com"
    # SENDER_PASSWORD = "你的163邮箱授权码"
    # RECEIVER_EMAIL = "收件人邮箱@example.com"

    # 示例：Outlook/Hotmail 邮箱配置 (可能需要开启SMTP服务和生成应用密码)
    # SENDER_EMAIL = "你的Outlook邮箱@outlook.com"
    # SENDER_PASSWORD = "你的Outlook应用密码"
    # RECEIVER_EMAIL = "收件人邮箱@example.com"

    # 示例3: 延迟 10 分钟 (600 秒) 关机，优先使用自定义命令，并发送邮件报告
    schedule_shutdown(
        delay_seconds=60000000,
        prefer_custom_command=True,
        send_email_report=True,
        email_account=SENDER_EMAIL,
        email_password=SENDER_PASSWORD,
        recipient_email=RECEIVER_EMAIL
    )

    print("\n--- 脚本执行结束 ---")