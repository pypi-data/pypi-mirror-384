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
    sender_email: str,
    sender_password: str,
    receiver_email: str,
    subject: str,
    body: str,
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
            logger.info(f"成功将日志文件 {attachment_path} 附加到邮件。")
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
        logger.info(f"邮件报告成功发送到: {receiver_email}")
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

