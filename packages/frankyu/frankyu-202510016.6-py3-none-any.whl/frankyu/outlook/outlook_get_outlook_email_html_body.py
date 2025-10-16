import win32com.client
import time

def get_outlook_email_html_body():
    """
    获取当前选中的 Outlook 邮件的 HTML 正文。

    Returns:
        str: 如果有选中的邮件，则返回其 HTML 正文；否则返回 None。
    """
    try:
        outlook_app = win32com.client.Dispatch("Outlook.Application")
        time.sleep(2)  # 稍微等待 Outlook 初始化

        explorer = outlook_app.ActiveExplorer()
        selection = explorer.Selection

        if len(selection) > 0:
            mail_item = selection.Item(1)
            return mail_item.HTMLBody
        else:
            print("没有选中的邮件。")
            return None

    except Exception as e:
        print(f"发生错误: {e}")
        return None

# 使用函数
if __name__ == "__main__":
    html_content = get_outlook_email_html_body()
    if html_content:
        print("获取到的 HTML 正文：")
        print(html_content)