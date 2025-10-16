import os
# 导入os模块

import datetime
# 导入datetime模块

import sys
# 导入sys模块

import time
# 导入time模块

import logging
# 导入logging模块

import smtplib
# 导入smtplib模块

import email.mime.text
# 导入email.mime.text模块

import email.mime.multipart
# 导入email.mime.multipart模块

import email.mime.base
# 导入email.mime.base模块，用于附件处理

import platform
# 导入platform模块

import subprocess
# 导入subprocess模块

import tempfile
# 导入tempfile模块

import socket
# 导入socket模块

import locale
# 导入locale模块

try:
    import netifaces
    # 尝试导入netifaces模块
except ImportError:
    netifaces = None
    # 如果导入失败，将netifaces设为None

try:
    import psutil
    # 尝试导入psutil模块
except ImportError:
    psutil = None
    # 如果导入失败，将psutil设为None

import urllib.request
# 导入urllib.request模块

logger = logging.getLogger(__name__)
# 创建日志记录器对象

logger.setLevel(logging.INFO)
# 设置日志级别为INFO

if logger.hasHandlers():
    logger.handlers.clear()
    # 如果日志记录器已有处理器，则清除它们

console_handler = logging.StreamHandler(sys.stdout)
# 创建控制台日志处理器，输出到标准输出

console_handler.setLevel(logging.INFO)
# 设置控制台处理器日志级别为INFO

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# 创建日志格式

console_handler.setFormatter(formatter)
# 设置控制台处理器的日志格式

logger.addHandler(console_handler)
# 添加控制台处理器到日志记录器

def get_all_ips_by_socket():
    # 获取所有IP地址（socket方法）
    ip_list = []
    # 初始化IP列表
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            # 遍历所有地址信息
            ip = info[4][0]
            # 获取IP地址
            if ':' not in ip and ip not in ip_list:
                # 排除IPv6和重复
                ip_list.append(ip)
                # 添加到IP列表
    except Exception as e:
        logger.warning(f"遍历所有IP时发生错误: {e}")
        # 记录警告日志
    return ip_list
    # 返回IP列表

def get_ips_by_netifaces():
    # 获取所有IP地址（netifaces方法）
    ip_list = []
    # 初始化IP列表
    if netifaces is None:
        logger.info("未安装netifaces库，跳过该方法。")
        # 记录信息日志
        return ip_list
        # 返回空列表
    try:
        for iface in netifaces.interfaces():
            # 遍历所有接口
            addrs = netifaces.ifaddresses(iface)
            # 获取接口地址
            for family in (netifaces.AF_INET, netifaces.AF_INET6):
                # 遍历IPv4和IPv6
                if family in addrs:
                    # 如果存在该协议族
                    for addr in addrs[family]:
                        # 遍历地址
                        ip = addr.get('addr')
                        # 获取IP地址
                        if ip and ':' not in ip and ip not in ip_list:
                            # 排除IPv6和重复
                            ip_list.append(ip)
                            # 添加到IP列表
    except Exception as e:
        logger.warning(f"netifaces获取IP时发生错误: {e}")
        # 记录警告日志
    return ip_list
    # 返回IP列表

def get_ips_by_psutil():
    # 获取所有IP地址（psutil方法）
    ip_list = []
    # 初始化IP列表
    if psutil is None:
        logger.info("未安装psutil库，跳过该方法。")
        # 记录信息日志
        return ip_list
        # 返回空列表
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            # 遍历所有接口及地址
            for addr in addrs:
                # 遍历地址
                ip = addr.address
                # 获取IP地址
                if addr.family == socket.AF_INET and ip not in ip_list:
                    # 仅IPv4且不重复
                    ip_list.append(ip)
                    # 添加到IP列表
    except Exception as e:
        logger.warning(f"psutil获取IP时发生错误: {e}")
        # 记录警告日志
    return ip_list
    # 返回IP列表

def get_external_ip():
    # 获取外部IP地址
    try:
        with urllib.request.urlopen("https://api.ipify.org") as response:
            # 请求外部服务
            return response.read().decode().strip()
            # 返回外部IP
    except Exception as e:
        logger.warning(f"无法获取外部IP: {e}")
        # 记录警告日志
        return "无法获取外部IP"
        # 返回错误提示

def get_system_info():
    # 获取系统信息
    system_info = {}
    # 初始化系统信息字典

    try:
        local_ip = socket.gethostbyname(socket.gethostname())
        # 获取本地IP地址
        system_info["IP Address (Local - Socket)"] = local_ip
        # 记录本地IP
        logger.info(f"成功使用socket获取本地IP地址: {local_ip}")
        # 日志输出
    except socket.gaierror:
        system_info["IP Address (Local - Socket)"] = "无法解析主机名或无网络连接"
        # 记录错误信息
        logger.warning("无法使用socket解析主机名获取本地IP。")
        # 日志输出
    except Exception as e:
        system_info["IP Address (Local - Socket)"] = f"获取本地IP时发生错误: {e}"
        # 记录错误信息
        logger.warning(f"使用socket获取本地IP时发生意外错误: {e}")
        # 日志输出

    all_ips = get_all_ips_by_socket()
    # 获取所有IP
    if all_ips:
        system_info["All IP Addresses (Socket)"] = ", ".join(all_ips)
        # 记录所有IP

    netifaces_ips = get_ips_by_netifaces()
    # 获取netifaces IP
    if netifaces_ips:
        system_info["IP Addresses (Netifaces)"] = ", ".join(netifaces_ips)
        # 记录netifaces IP

    psutil_ips = get_ips_by_psutil()
    # 获取psutil IP
    if psutil_ips:
        system_info["IP Addresses (Psutil)"] = ", ".join(psutil_ips)
        # 记录psutil IP

    external_ip = get_external_ip()
    # 获取外部IP
    system_info["External IP"] = external_ip
    # 记录外部IP

    system_info["Computer Name"] = platform.node()
    # 获取计算机名

    try:
        if sys.platform.startswith('win'):
            cpu_output = subprocess.check_output(
                "wmic cpu get Name /value",
                shell=True,
                text=True,
                encoding='utf-8',
                stderr=subprocess.PIPE
            )
            # Windows下获取CPU信息
            name_line = [line for line in cpu_output.splitlines() if line.startswith('Name=')]
            # 查找CPU名称行
            if name_line:
                system_info["CPU Info"] = name_line[0].split('=')[1].strip()
                # 记录CPU信息
            else:
                system_info["CPU Info"] = cpu_output.strip()
                # 记录原始输出
        elif sys.platform.startswith('darwin'):
            cpu_output = subprocess.check_output(
                "sysctl -n machdep.cpu.brand_string",
                shell=True,
                text=True,
                encoding='utf-8',
                stderr=subprocess.PIPE
            )
            # macOS下获取CPU信息
            system_info["CPU Info"] = cpu_output.strip()
            # 记录CPU信息
        else:
            cpu_output = subprocess.check_output(
                "grep -m 1 'model name' /proc/cpuinfo",
                shell=True,
                text=True,
                encoding='utf-8',
                stderr=subprocess.PIPE
            )
            # Linux下获取CPU信息
            system_info["CPU Info"] = cpu_output.split(":")[1].strip()
            # 记录CPU信息
    except Exception as e:
        system_info["CPU Info"] = f"未能检索CPU信息: {e}"
        # 记录错误信息
        logger.error(f"检索CPU信息时发生错误: {e}")
        # 日志输出

    system_info["Python Version"] = sys.version
    # 获取Python版本

    system_info["Python Path"] = sys.executable
    # 获取Python可执行路径

    return system_info
    # 返回系统信息字典

def send_shutdown_email(
    sender_email: str="yurx17@qq.com",
    sender_password: str="tltpcwaacooocffe",
    receiver_email: str="yufengguang@hotmail.com",
    subject: str="标题",
    body: str="正文",
    attachment_path: str = None
):
    # 发送关机报告邮件
    if not sender_email or not sender_password or not receiver_email:
        logger.error("发件人邮箱、密码或收件人邮箱缺失。跳过邮件发送。")
        # 参数校验
        return
        # 跳过发送

    smtp_server = None
    # SMTP服务器
    smtp_port = None
    # SMTP端口
    use_ssl = False
    # 是否使用SSL

    email_domain = sender_email.split('@')[-1].lower()
    # 获取邮箱域名

    if "qq.com" in email_domain:
        smtp_server = "smtp.qq.com"
        smtp_port = 587
        use_ssl = False
        logger.info(f"检测到QQ邮箱，使用配置: {smtp_server}:{smtp_port} (STARTTLS)")
    elif "gmail.com" in email_domain:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        use_ssl = False
        logger.info(f"检测到Gmail，使用配置: {smtp_server}:{smtp_port} (STARTTLS)")
    elif "163.com" in email_domain:
        smtp_server = "smtp.163.com"
        smtp_port = 465
        use_ssl = True
        logger.info(f"检测到163邮箱，使用配置: {smtp_server}:{smtp_port} (SSL)")
    elif ("outlook.com" in email_domain or
          "hotmail.com" in email_domain or
          "office365.com" in email_domain):
        smtp_server = "smtp.office365.com"
        smtp_port = 587
        use_ssl = False
        logger.info(f"检测到Outlook/Hotmail/Office365邮箱，使用配置: {smtp_server}:{smtp_port} (STARTTLS)")
    else:
        logger.warning(f"无法识别的发件人邮箱域名 '{email_domain}'。尝试通用SMTP配置 (smtp.yourdomain.com:587)。")
        smtp_server = f"smtp.{email_domain}"
        smtp_port = 587
        use_ssl = False

    if not smtp_server or not smtp_port:
        logger.error("无法确定邮件服务器配置。请手动指定或检查发件人邮箱域名。")
        return

    msg = email.mime.multipart.MIMEMultipart()
    # 创建邮件对象
    msg['From'] = sender_email
    # 设置发件人
    msg['To'] = receiver_email
    # 设置收件人
    msg['Subject'] = subject
    # 设置主题

    msg.attach(email.mime.text.MIMEText(body, 'plain', 'utf-8'))
    # 添加邮件正文

    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as f:
                attachment_content = f.read().decode('utf-8', errors='ignore')
                attachment = email.mime.text.MIMEText(attachment_content, 'plain', 'utf-8')
                attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
            msg.attach(attachment)
            logger.info(f"成功将文件 {attachment_path} 附加到邮件。")
        except Exception as e:
            logger.warning(f"未能将 {attachment_path} 附加到邮件: {e}")
    else:
        if attachment_path:
            logger.warning(f"附件文件 {attachment_path} 不存在或路径无效。邮件将不包含此附件。")

    try:
        server = None
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        logger.info(f"邮件成功发送到: {receiver_email}")
    except smtplib.SMTPAuthenticationError:
        logger.error("邮件认证失败。请检查您的邮箱账户和**授权码/密码**，并确保SMTP服务已启用。")
    except smtplib.SMTPConnectError as e:
        error_message = f"无法连接到SMTP服务器 '{smtp_server}:{smtp_port}'。"
        if isinstance(e.__cause__, socket.gaierror):
            error_message += "这通常意味着服务器地址无法解析或没有网络连接。 请检查您的网络连接、DNS设置或防火墙。"
        else:
            error_message += "请检查SMTP服务器地址和端口，以及网络连接和防火墙。"
        error_message += f" 原始错误: {e}"
        logger.error(error_message)
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"SMTP服务器意外断开连接: {e}。请检查网络稳定性或服务器配置。")
    except smtplib.SMTPException as e:
        logger.error(f"邮件发送过程中发生SMTP协议错误: {e}")
    except socket.timeout:
        logger.error(f"连接到SMTP服务器 '{smtp_server}:{smtp_port}' 超时。请检查网络或服务器状态。")
    except Exception as e:
        logger.error(f"邮件发送过程中发生未知错误: {e}")

def schedule_shutdown(
    delay_seconds: int = 60,
    prefer_custom_command: bool = True,
    send_email_report: bool = True,
    email_account: str = "yurx17@qq.com",
    email_password: str = "tltpcwaacooocffe",
    recipient_email: str = "yufengguang@hotmail.com"
) -> bool:
    # 安排关机并发送报告
    default_log_base_dir = "shutdown_logs"
    log_base_dir = default_log_base_dir
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    try:
        os.makedirs(log_base_dir, exist_ok=True)
        logger.info(f"日志目录已确保存在: {log_base_dir}")
    except PermissionError:
        logger.warning(f"当前工作目录 '{os.getcwd()}' 没有写入权限。尝试系统临时目录。")
        temp_dir = tempfile.gettempdir()
        log_base_dir = os.path.join(temp_dir, "shutdown_logs_temp")
        try:
            os.makedirs(log_base_dir, exist_ok=True)
            logger.info(f"日志目录已确保存在于临时目录中: {log_base_dir}")
        except Exception as e:
            error_msg = f"错误: 无法在系统临时目录 '{temp_dir}' 中创建日志目录 '{log_base_dir}': {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
    except Exception as e:
        error_msg = f"错误: 无法创建日志目录 '{log_base_dir}': {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

    log_filename = os.path.join(log_base_dir, f"shutdown_script_{timestamp_str}.log")
    log_file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    log_file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file_handler.setFormatter(formatter)
    logger.addHandler(log_file_handler)

    logger.info(f"函数执行开始: 延迟={delay_seconds}s, 偏好自定义={prefer_custom_command}。 日志保存到: {log_filename}")

    _has_custom_command_module = False
    cm = None
    if prefer_custom_command:
        try:
            import frankyu.cmd.command_execute as loaded_cm
            cm = loaded_cm
            _has_custom_command_module = True
            logger.info("成功导入frankyu.cmd.command_execute模块。")
        except ImportError:
            logger.warning("无法导入frankyu.cmd.command_execute模块。 将尝试使用os.system。")
        except Exception as e:
            logger.error(f"导入frankyu.cmd.command_execute模块时发生未知错误: {e}。 将尝试使用os.system。")

    try:
        delay_seconds = int(delay_seconds)
        if delay_seconds < 0:
            error_msg = f"错误: 延迟时间 (delay_seconds) 不能为负数。 接收到: {delay_seconds}"
            logger.error(error_msg)
            if send_email_report:
                system_info = get_system_info()
                system_info_text = "\n--- 系统信息 ---\n"
                for key, value in system_info.items():
                    system_info_text += f"{key}: {value}\n"
                system_info_text += "--------------------"
                send_shutdown_email(
                    email_account,
                    email_password,
                    recipient_email,
                    f"关机计划失败 - 参数错误 - {datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                    error_msg + "\n" + system_info_text,
                    log_filename
                )
            return False
    except ValueError:
        error_msg = f"错误: 延迟时间 (delay_seconds) 必须是有效的整数。 接收到: {delay_seconds}"
        logger.error(error_msg)
        if send_email_report:
            system_info = get_system_info()
            system_info_text = "\n--- 系统信息 ---\n"
            for key, value in system_info.items():
                system_info_text += f"{key}: {value}\n"
            system_info_text += "--------------------"
            send_shutdown_email(
                email_account,
                email_password,
                recipient_email,
                f"关机计划失败 - 参数错误 - {datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                error_msg + "\n" + system_info_text,
                log_filename
            )
        return False

    output_filename_with_timestamp = os.path.join(log_base_dir, f"shutdown_info_{timestamp_str}.txt")

    shutdown_command_prefix = ""
    abort_command = ""
    ping_command = ""
    command_separator = ""
    full_shutdown_command = ""

    if sys.platform.startswith('win'):
        shutdown_command_prefix = "shutdown -s -t"
        abort_command = "shutdown -a"
        ping_command = "ping 127.0.0.1 -n 1"
        command_separator = "&"
        full_shutdown_command = f"{abort_command} {command_separator} {ping_command} {command_separator} {shutdown_command_prefix} {delay_seconds}"
    elif sys.platform.startswith('darwin'):
        abort_command = "echo '在macOS上取消计划关机可能需要手动干预，例如，杀死相关关机进程或使用 'sudo killall shutdown'.'"
        shutdown_command_prefix = "sudo shutdown -h +"
        ping_command = "ping -c 1 127.0.0.1"
        command_separator = ";"
        delay_minutes = max(1, (delay_seconds + 59) // 60)
        full_shutdown_command = f"{abort_command} {command_separator} {ping_command} {command_separator} {shutdown_command_prefix}{delay_minutes}"
        logger.warning("在macOS上执行'sudo shutdown'通常需要管理员密码。")
    else:
        shutdown_command_prefix = "sudo shutdown -h +"
        abort_command = "sudo shutdown -c"
        ping_command = "ping -c 1 127.0.0.1"
        command_separator = ";"
        delay_minutes = max(1, (delay_seconds + 59) // 60)
        full_shutdown_command = f"{abort_command} {command_separator} {ping_command} {command_separator} {shutdown_command_prefix}{delay_minutes}"
        logger.warning("在Linux上执行'sudo shutdown'通常需要管理员密码。")

    logger.info(f"检测到操作系统: {sys.platform}。 构建的命令: {full_shutdown_command}")

    now = datetime.datetime.now()
    endtime = now + datetime.timedelta(seconds=delay_seconds)

    system_info = get_system_info()
    system_info_text = "\n--- 系统信息 ---\n"
    for key, value in system_info.items():
        system_info_text += f"{key}: {value}\n"
    system_info_text += "--------------------"

    output_text = (
        f'''--- 关机计划详情 ---\n\n'''
        f'''启动时间: {now.strftime("%Y-%m-%d %H:%M:%S")}\n'''
        f'''延迟时长: {datetime.timedelta(seconds=delay_seconds)} ({delay_seconds} 秒)\n'''
        f'''预计关机时间: {endtime.strftime("%Y-%m-%d %H:%M:%S")}\n'''
        f'''操作系统: {sys.platform}\n'''
        f'''将执行的命令: {full_shutdown_command}\n\n'''
        f'''{system_info_text}\n'''
        f'''--------------------'''
    )

    try:
        with open(output_filename_with_timestamp, "w", encoding="utf-8") as f:
            f.write(output_text)
        logger.info(f"关机信息成功保存到 {output_filename_with_timestamp}")
    except PermissionError:
        error_msg = f"错误: 没有权限写入文件 {output_filename_with_timestamp}。"
        logger.error(error_msg)
        if send_email_report:
            send_shutdown_email(
                email_account,
                email_password,
                recipient_email,
                f"关机计划失败 - 文件权限错误 - {datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                error_msg + "\n" + system_info_text,
                log_filename
            )
        return False
    except IOError as e:
        error_msg = f"写入文件 {output_filename_with_timestamp} 时发生I/O错误: {e}"
        logger.error(error_msg)
        if send_email_report:
            send_shutdown_email(
                email_account,
                email_password,
                recipient_email,
                f"关机计划失败 - 文件写入错误 - {datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                error_msg + "\n" + system_info_text,
                log_filename
            )
        return False
    except Exception as e:
        error_msg = f"写入文件 {output_filename_with_timestamp} 时发生未知错误: {e}"
        logger.error(error_msg)
        if send_email_report:
            send_shutdown_email(
                email_account,
                email_password,
                recipient_email,
                f"关机计划失败 - 未知文件错误 - {datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                error_msg + "\n" + system_info_text,
                log_filename
            )
        return False

    print(output_text)

    command_executed_successfully = False
    execution_detail = ""
    stdout_output_str = ""
    stderr_output_str = ""
    command_return_code = -1

    if prefer_custom_command and _has_custom_command_module:
        logger.info(f"尝试通过frankyu.cmd.command_execute执行命令 (首选模式): {full_shutdown_command}")
        try:
            stdout_raw, stderr_raw, return_code_raw = cm.execute_command(full_shutdown_command)
            stdout_output_str = str(stdout_raw).strip() if stdout_raw is not None else ""
            stderr_output_str = str(stderr_raw).strip() if stderr_raw is not None else ""
            try:
                command_return_code = int(return_code_raw)
            except (ValueError, TypeError):
                command_return_code = -1
                logger.warning(f"无法将命令退出码 '{return_code_raw}' 转换为整数。将其视为失败。")
            if command_return_code == 0:
                execution_detail = "frankyu.cmd.command_execute命令执行成功。"
                logger.info(execution_detail)
                logger.info(f"命令输出 (stdout):\n{stdout_output_str}")
                logger.info(f"命令错误 (stderr):\n{stderr_output_str}")
                command_executed_successfully = True
            else:
                execution_detail = (
                    f"frankyu.cmd.command_execute命令执行失败。退出码: {command_return_code}\n"
                    f"命令输出 (stdout):\n{stdout_output_str}\n"
                    f"命令错误 (stderr):\n{stderr_output_str}"
                )
                logger.error(execution_detail)
        except PermissionError:
            execution_detail = "通过frankyu.cmd.command_execute执行时权限被拒绝。将尝试回退到os.system。"
            logger.warning(execution_detail)
        except Exception as e:
            execution_detail = f"通过frankyu.cmd.command_execute执行命令时发生异常: {e}。"
            logger.warning(execution_detail)
        finally:
            print(f"\n--- 尝试通过frankyu.cmd.command_execute执行命令 (首选模式) ---")
            print(f"运行命令: {full_shutdown_command}")
            print(f"命令输出 (stdout):\n{stdout_output_str if stdout_output_str else '无'}")
            print(f"命令错误 (stderr):\n{stderr_output_str if stderr_output_str else '无'}")
            print(f"命令退出码: {command_return_code}")
            if command_executed_successfully:
                print(f"✅ {execution_detail.splitlines()[0]}")
            else:
                print(f"❌ {execution_detail.splitlines()[0]}")

    if not command_executed_successfully:
        if prefer_custom_command and not _has_custom_command_module:
            logger.info("无法使用frankyu.cmd.command_execute (模块未导入)。将直接使用os.system。")
        elif prefer_custom_command and _has_custom_command_module:
            logger.info("frankyu.cmd.command_execute失败或遇到异常，回退到os.system。")
        else:
            logger.info("不偏好自定义命令。直接使用os.system。")

        logger.info(f"尝试通过os.system执行命令: {full_shutdown_command}")
        print(f"\n--- 尝试通过os.system执行命令 ---")
        print(f"运行命令: {full_shutdown_command}")
        try:
            command_return_code = os.system(full_shutdown_command)
            if command_return_code != 0:
                execution_detail = f"os.system命令执行失败。退出码: {command_return_code}"
                logger.error(execution_detail)
                if (sys.platform.startswith('darwin') or sys.platform.startswith('linux')):
                    logger.warning("提示: 这可能是由于缺少'sudo'权限或需要输入密码。请确保您拥有必要的权限。")
                command_executed_successfully = False
            else:
                execution_detail = "os.system命令执行成功。"
                logger.info(execution_detail)
                command_executed_successfully = True
        except Exception as e:
            execution_detail = f"通过os.system执行命令时发生异常: {e}"
            logger.error(execution_detail)
            command_executed_successfully = False
        finally:
            if command_executed_successfully:
                print(f"✅ {execution_detail}")
            else:
                print(f"❌ {execution_detail}")

    final_status_msg = ""
    if not command_executed_successfully:
        final_status_msg = "关机命令未能执行。 请检查上面的错误信息。"
        logger.error(f"最终状态: {final_status_msg}")
        print(f"\n🚫 警告: **{final_status_msg}**")
        if send_email_report:
            current_time_for_subject = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            send_shutdown_email(
                email_account,
                email_password,
                recipient_email,
                f"关机计划失败 - {current_time_for_subject}",
                final_status_msg + "\n" + execution_detail + "\n" + output_text,
                log_filename
            )
        return False
    else:
        final_status_msg = "关机命令成功发送。"
        logger.info(f"最终状态: {final_status_msg}")
        print(f"\n🎉 成功: **{final_status_msg}**")
        if send_email_report:
            current_time_for_subject = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            send_shutdown_email(
                email_account,
                email_password,
                recipient_email,
                f"关机计划成功 - {current_time_for_subject}",
                final_status_msg + "\n" + output_text,
                log_filename
            )
        return True

if __name__ == "__main__":
    print("--- 脚本执行开始 ---")
    SENDER_EMAIL = "yurx17@qq.com"
    SENDER_PASSWORD = "tltpcwaacooocffe"
    RECEIVER_EMAIL = "yufengguang@hotmail.com"
    test_delay_seconds = 600000
    schedule_shutdown(
        delay_seconds=test_delay_seconds,
        prefer_custom_command=True,
        send_email_report=True,
        email_account=SENDER_EMAIL,
        email_password=SENDER_PASSWORD,
        recipient_email=RECEIVER_EMAIL
    )
    print("\n--- 脚本执行结束 ---")