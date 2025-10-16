import mail_send_shutdown_email_8 as mail
import system_get_system_info as sysinfo

def send_system_info_email(subject="ip"):
    """
    获取系统信息并通过邮件发送。

    参数:
        subject (str): 邮件主题，默认 "ip"
    """
    # 获取系统信息字典
    system_info_dict = sysinfo.get_system_info()
    info_list = []
    # 将 key 和 value 依次加入列表
    for key, value in system_info_dict.items():
        info_list.append(key)
        info_list.append(value)
    # 以换行拼接所有内容
    info_text = "\n".join(info_list)
    # 按逗号分割再换行，并去除空格（可选，未实际发送）
    formatted_text = "\n".join(info_text.split(","))
    formatted_text = formatted_text.replace(" ", "")
    # 发送邮件，正文为 formatted_text
    mail.send_shutdown_email(subject=subject, body=formatted_text)

if __name__ == "__main__":
    # 主程序入口，运行时发送系统信息邮件
    send_system_info_email()
import time
#time.sleep(5)