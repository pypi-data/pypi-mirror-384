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
    #receiver_email: str="frank_yu@prime3c.com",
    receiver_email: str="yufengguang@hotmail.com",
    
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
        #smtp_port = 465
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

    elif "prime3c.com" in email_domain:
        smtp_server = "owa.prime3c.com"
        smtp_port = 465 # 163也支持587+STARTTLS
        #smtp_port = 587 # 163也支持587+STARTTLS
        use_ssl = True
        #use_ssl = 0
        logger.info(f"检测到 prime3c.com 邮箱，使用配置: {smtp_server}:{smtp_port} (SSL)")


        
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
    msg.attach(MIMEText(body, 'html', 'utf-8')) # 主体内容 #123123

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
        print(f"✅ 邮件已成功发送至: **{receiver_email}**")
        logger.info(f"邮件已成功发送至: {receiver_email}")
    except smtplib.SMTPAuthenticationError:#123123
        print("❌ 错误: 邮件身份验证失败。请检查邮箱账号和**授权码/密码**是否正确，并确保已开启SMTP服务。")
        logger.error("邮件身份验证失败。请检查邮箱账号和**授权码/密码**是否正确，并确保已开启SMTP服务。")
    except smtplib.SMTPConnectError as e:
        print(f"❌ 错误: 无法连接到SMTP服务器 '{smtp_server}:{smtp_port}'。请检查SMTP服务器地址和端口，以及网络连接和防火墙。错误: {e}")
        logger.error(f"无法连接到SMTP服务器 '{smtp_server}:{smtp_port}'。请检查SMTP服务器地址和端口，以及网络连接和防火墙。错误: {e}")
    except Exception as e:
        print(f"❌ 邮件发送过程中发生未知错误: {e}")
        logger.error(f"邮件发送过程中发生未知错误: {e}")


