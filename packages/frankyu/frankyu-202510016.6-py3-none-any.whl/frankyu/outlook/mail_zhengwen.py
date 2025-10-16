import pythoncom
# 导入 pythoncom 模块，用于处理 COM (Component Object Model) 对象

import win32com.client
# 导入 win32com.client 模块，用于与 Windows 应用程序（如 Outlook）进行交互

from datetime import datetime
# 导入 datetime 模块，用于处理日期和时间

import os
# 导入 os 模块，用于处理操作系统相关的功能


def initialize_outlook():
    """
    初始化 Outlook 应用程序并获取 MAPI 命名空间。
    
    思路:
    1. 调用 pythoncom.CoInitialize() 初始化 COM 库。
    2. 使用 win32com.client.Dispatch 创建 Outlook 应用程序的 COM 对象。
    3. 调用 outlook.GetNamespace("MAPI") 获取 MAPI 命名空间。
    4. 添加异常处理，捕获 COM 错误或其他异常。

    方法清单:
    - pythoncom.CoInitialize(): 初始化 COM 库。
    - win32com.client.Dispatch("Outlook.Application"): 创建 Outlook COM 对象。
    - outlook.GetNamespace("MAPI"): 获取 MAPI 命名空间。
    - pythoncom.com_error: 捕获 COM 相关错误。

    返回值:
        mapi: Outlook 的 MAPI 命名空间对象，如果初始化成功。
        None: 如果初始化失败。
    """
    try:
        pythoncom.CoInitialize()
        # 初始化 COM 库

        outlook = win32com.client.Dispatch("Outlook.Application")
        # 创建 Outlook 应用程序的 COM 对象

        mapi = outlook.GetNamespace("MAPI")
        # 获取 Outlook 的 MAPI 命名空间

        return mapi
        # 返回 MAPI 命名空间对象

    except pythoncom.com_error as e:
        # 捕获 COM 错误

        print(f"COM 错误: {e}")
        # 打印 COM 错误信息

        return None
        # 返回 None 表示初始化失败

    except Exception as e:
        # 捕获其他类型的异常

        print(f"初始化 Outlook 时发生其他错误: {str(e)}")
        # 打印其他错误信息

        return None
        # 返回 None 表示初始化失败


def find_outlook_account(mapi, account_email):
    """
    根据邮箱地址查找 Outlook 账户。

    思路:
    1. 遍历 MAPI 命名空间中的所有账户。
    2. 比较每个账户的 SMTP 地址是否与目标邮箱地址匹配（忽略大小写）。
    3. 若找到匹配账户，则返回该账户对象。
    4. 若未找到匹配账户，打印提示信息。

    方法清单:
    - mapi.Accounts: 获取所有 Outlook 账户。
    - account.SmtpAddress: 获取账户的 SMTP 地址。
    - account_email.lower(): 将邮箱地址转换为小写进行比较。

    参数:
        mapi: Outlook 的 MAPI 命名空间对象。
        account_email: 要查找的邮箱账户的电子邮件地址（字符串）。

    返回值:
        account: 匹配的 Outlook 账户对象。
        None: 如果未找到匹配的账户。
    """
    if mapi:
        # 检查 MAPI 命名空间是否有效

        for account in mapi.Accounts:
            # 遍历 MAPI 中的所有账户

            if account.SmtpAddress.lower() == account_email.lower():
                # 比较账户的 SMTP 地址是否与目标邮箱地址匹配

                return account
                # 返回匹配的账户对象

        print(f"未找到邮箱账户: {account_email}")
        # 如果未找到匹配账户，打印提示信息

    return None
    # 如果未找到账户或 MAPI 无效，返回 None


def get_folder_by_name(account, folder_name):
    """
    根据账户和文件夹名称获取 Outlook 文件夹对象。

    思路:
    1. 检查是否是收件箱或已发送邮件的特殊文件夹，直接返回对应的默认文件夹。
    2. 若是其他文件夹名称，尝试通过名称查找匹配的文件夹。
    3. 添加异常处理，捕获无法找到文件夹的错误。

    方法清单:
    - account.DeliveryStore.GetDefaultFolder(6): 获取默认的收件箱文件夹。
    - account.DeliveryStore.GetDefaultFolder(5): 获取默认的已发送邮件文件夹。
    - account.DeliveryStore.Folders(folder_name): 按名称获取自定义文件夹。
    - folder.Name: 获取文件夹名称。

    参数:
        account: Outlook 账户对象。
        folder_name: 要获取的文件夹的名称（字符串）。

    返回值:
        folder: 对应的 Outlook 文件夹对象。
        None: 如果未找到匹配的文件夹。
    """
    if account:
        # 检查账户对象是否有效

        try:
            if folder_name == "Inbox":
                # 如果文件夹名称是 "Inbox"

                return account.DeliveryStore.GetDefaultFolder(6)
                # 返回默认的收件箱文件夹（编号 6）

            elif folder_name == "Sent Items":
                # 如果文件夹名称是 "Sent Items"

                return account.DeliveryStore.GetDefaultFolder(5)
                # 返回默认的已发送邮件文件夹（编号 5）

            else:
                # 如果是其他文件夹名称

                try:
                    folder = account.DeliveryStore.Folders(folder_name)
                    # 按名称获取自定义文件夹

                    print(f"成功找到文件夹: {folder.Name}")
                    # 打印成功找到的文件夹名称

                    return folder
                    # 返回找到的文件夹对象

                except Exception as e:
                    # 捕获未找到文件夹时的异常

                    print(f"未找到指定文件夹 '{folder_name}': {str(e)}")
                    # 打印错误信息

                    return None
                    # 返回 None 表示未找到文件夹

        except Exception as e:
            # 捕获其他异常

            print(f"获取文件夹时出错: {str(e)}")
            # 打印错误信息

            return None
            # 返回 None 表示获取文件夹失败

    return None
    # 如果账户对象无效，返回 None


def get_emails(folder):
    """
    从指定的 Outlook 文件夹获取邮件列表并按接收时间排序。

    思路:
    1. 使用文件夹对象的 Items 属性获取所有邮件。
    2. 调用 Sort 方法按邮件接收时间降序排列。
    3. 添加异常处理，捕获可能的错误。

    方法清单:
    - folder.Items: 获取文件夹中的所有项目。
    - items.Sort("[ReceivedTime]", True): 按接收时间降序排列邮件列表。

    参数:
        folder: Outlook 文件夹对象。

    返回值:
        items: 包含邮件的集合对象。
        None: 如果获取失败或文件夹无效。
    """
    if folder:
        # 检查文件夹对象是否有效

        try:
            items = folder.Items
            # 获取文件夹中的所有项目（包括邮件）

            items.Sort("[ReceivedTime]", True)
            # 按接收时间降序排列邮件列表

            return items
            # 返回排序后的邮件集合

        except Exception as e:
            # 捕获获取邮件列表时的异常

            print(f"获取邮件列表时出错: {str(e)}")
            # 打印错误信息

            return None
            # 返回 None 表示获取失败

    return None
    # 如果文件夹无效，返回 None


def print_email_info(email, folder_name, index):
    """
    打印单封邮件的信息，包括主题、发件人/收件人、接收时间、正文前三行和附件名称。

    思路:
    1. 打印邮件的索引和主题。
    2. 根据文件夹类型，分别打印发件人或收件人信息。
    3. 打印邮件的接收时间。
    4. 打印邮件正文的前三行。
    5. 打印邮件的附件名称。
    6. 添加异常处理，处理可能缺失的属性。

    方法清单:
    - email.Subject: 获取邮件主题。
    - email.SenderName: 获取发件人名称。
    - email.To: 获取收件人信息。
    - email.ReceivedTime: 获取接收时间。
    - email.Body: 获取邮件正文。
    - email.Attachments: 获取附件集合。

    参数:
        email: Outlook 邮件对象。
        folder_name: 邮件所在的文件夹名称（字符串）。
        index: 邮件在列表中的索引（整数）。

    返回值:
        无
    """
    print(f"邮件 {index}:")
    # 打印邮件的索引

    try:
        print(f"  主题: {email.Subject}")
        # 打印邮件主题

    except AttributeError:
        # 如果 Subject 属性不存在

        print("  主题: 无法获取")
        # 打印错误信息

    if folder_name == "Sent Items":
        # 如果是已发送邮件

        try:
            print(f"  收件人: {email.To}")
            # 打印收件人信息

        except AttributeError:
            # 如果 To 属性不存在

            try:
                print(f"  发件人 (尝试 Sender): {email.Sender}")
                # 尝试打印发件人信息

            except AttributeError:
                # 如果 Sender 属性不存在

                try:
                    print(f"  发件人 (尝试 SenderName): {email.SenderName}")
                    # 尝试打印发件人名称

                except AttributeError:
                    # 如果 SenderName 属性也不存在

                    print("  无法获取发件人/收件人信息")
                    # 打印错误信息

    else:
        # 如果是其他文件夹

        try:
            print(f"  发件人: {email.SenderName}")
            # 打印发件人信息

        except AttributeError:
            # 如果 SenderName 属性不存在

            try:
                print(f"  发件人 (尝试 Sender): {email.Sender}")
                # 尝试打印发件人信息

            except AttributeError:
                # 如果 Sender 属性不存在

                print("  无法获取发件人信息")
                # 打印错误信息

    try:
        print(f"  接收时间: {email.ReceivedTime}")
        # 打印接收时间

    except AttributeError:
        # 如果 ReceivedTime 属性不存在

        print("  接收时间: 无法获取")
        # 打印错误信息

    try:
        body = email.Body
        # 获取邮件正文

        body_lines = body.splitlines()
        # 分割正文为行列表

        print("  正文前三行:")
        # 打印正文前三行标题

        for i, line in enumerate(body_lines[:3]):
            # 遍历前三行正文

            print(f"    {line}")
            # 打印正文行

            if i == 2:
                break
                # 如果达到第三行，退出循环

        if not body_lines:
            # 如果正文为空

            print("    (正文为空)")
            # 打印正文为空的提示

        elif len(body_lines) < 3:
            # 如果正文不足三行

            print("    (正文不足三行)")
            # 打印正文不足三行的提示

    except AttributeError:
        # 如果 Body 属性不存在

        print("  正文: 无法获取")
        # 打印错误信息

    try:
        attachments = email.Attachments
        # 获取附件集合

        if attachments.Count > 0:
            # 如果附件数量大于 0

            print("  附件:")
            # 打印附件标题

            for attachment in attachments:
                # 遍历附件集合

                print(f"    - {attachment.FileName}")
                # 打印附件名称

        else:
            # 如果没有附件

            print("  附件: 无")
            # 打印附件为空的提示

    except AttributeError:
        # 如果 Attachments 属性不存在

        print("  附件: 无法获取")
        # 打印错误信息


def print_emails_in_folder(folder_name, emails):
    """
    打印指定文件夹中的所有邮件信息。

    思路:
    1. 检查邮件集合是否为空。
    2. 遍历集合并打印每封邮件的详细信息。
    3. 在遍历时调用 print_email_info 函数处理单封邮件的打印逻辑。

    方法清单:
    - len(emails): 获取邮件集合的大小。
    - enumerate(emails): 遍历邮件集合并生成索引。
    - print_email_info(): 打印单封邮件的详细信息。

    参数:
        folder_name: 邮件所在的文件夹名称（字符串）。
        emails: 包含 Outlook 邮件对象的集合。

    返回值:
        无
    """
    if emails:
        # 检查邮件列表是否为空

        print(f"\n成功获取到 {len(emails)} 封来自 '{folder_name}' 的邮件！")
        # 打印成功获取的邮件数量和文件夹名称

        for idx, email in enumerate(emails):
            # 遍历邮件列表，同时获取索引

            print_email_info(email, folder_name, idx + 1)
            # 调用 print_email_info 函数打印每封邮件的详细信息

    else:
        # 如果邮件列表为空或为 None

        print(f"未获取到 '{folder_name}' 中的邮件或发生错误。")
        # 打印未获取到邮件或发生错误的消息


def main():
    """
    主函数，用于获取指定邮箱账户的收件箱和已发送邮件信息并打印。

    思路:
    1. 初始化 Outlook 并获取 MAPI 命名空间。
    2. 遍历所有账户并打印账户信息。
    3. 根据邮箱地址查找指定账户。
    4. 获取收件箱和已发送邮件的信息，并分别打印。

    方法清单:
    - initialize_outlook(): 初始化 Outlook 并获取 MAPI。
    - find_outlook_account(): 根据邮箱地址查找账户。
    - get_folder_by_name(): 获取指定文件夹。
    - get_emails(): 获取邮件列表。
    - print_emails_in_folder(): 打印文件夹中的邮件信息。

    参数:
        无

    返回值:
        无
    """
    account_email = "Frank_Yu@prime3c.com"
    # 设置要访问的 Outlook 账户的电子邮件地址

    mapi = initialize_outlook()
    # 初始化 Outlook 并获取 MAPI 命名空间

    if mapi:
        # 如果 MAPI 初始化成功

        print("\n所有账户：")
        # 打印所有可用的 Outlook 账户信息

        for account in mapi.Accounts:
            print(f"  - 账户名称: {account.DisplayName}")
            print(f"    邮箱地址: {account.SmtpAddress}")
            print(f"    邮箱路径: {account.DeliveryStore.DisplayName}")

        account = find_outlook_account(mapi, account_email)
        # 根据邮箱地址查找 Outlook 账户

        if account:
            # 如果找到了指定的账户

            inbox_folder = get_folder_by_name(account, "Inbox")
            # 获取收件箱文件夹对象

            inbox_emails = get_emails(inbox_folder)
            # 获取收件箱中的邮件列表

            print_emails_in_folder("收件箱", inbox_emails)
            # 打印收件箱中的邮件信息

            sent_folder = get_folder_by_name(account, "Sent Items")
            # 获取已发送邮件文件夹对象

            sent_emails = get_emails(sent_folder)
            # 获取已发送邮件中的邮件列表

            print_emails_in_folder("已发送邮件", sent_emails)
            # 打印已发送邮件中的邮件信息

    pythoncom.CoUninitialize()
    # 取消初始化 COM 库，释放资源


if __name__ == "__main__":
    main()
    # 当脚本直接运行时，调用 main 函数