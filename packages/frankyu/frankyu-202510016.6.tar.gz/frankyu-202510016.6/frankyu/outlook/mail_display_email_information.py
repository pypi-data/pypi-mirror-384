def display_email_information(
    email_account="Frank_Yu@prime3c.com",
    english_folder_name="Inbox",
    chinese_folder_name="收件箱",
):
    """
    顯示指定郵箱帳戶中指定資料夾內的郵件資訊。

    思路:
    1. 初始化 Outlook API，獲取 MAPI 命名空間。
    2. 遍歷所有帳戶，列出帳戶的基本資訊（顯示名稱、郵箱地址、儲存路徑）。
    3. 查找目標郵箱帳戶，並確保找到有效帳戶。
    4. 獲取指定資料夾的對象，支持通過英文名稱查找。
    5. 獲取該資料夾中的所有郵件，並按時間排序。
    6. 輸出郵件的詳細資訊，使用指定的中文資料夾名稱作為輸出標題。

    方法清單:
    - f_mail.mail_biaoti.initialize_outlook(): 初始化 Outlook API 並獲取 MAPI 命名空間。
    - f_mail.mail_biaoti.find_outlook_account(): 根據郵箱地址查找目標帳戶。
    - f_mail.mail_biaoti.get_folder_by_name(): 根據名稱獲取郵箱資料夾對象。
    - f_mail.mail_biaoti.get_emails(): 獲取資料夾中的郵件列表。
    - f_mail.mail_biaoti.print_emails_in_folder(): 打印資料夾中的郵件資訊。

    參數:
        email_account (str): 郵箱帳戶地址，默認為 "Frank_Yu@prime3c.com"。
        english_folder_name (str): 郵箱資料夾的英文名稱，默認為 "Inbox"。例如 "Sent Items"。
        chinese_folder_name (str): 郵箱資料夾的中文名稱，默認為 "收件箱"。

    返回值:
        無
    """
    import f_mail.mail_biaoti  # 導入郵件處理模組

    mail_api = f_mail.mail_biaoti.initialize_outlook()
    # 初始化 Outlook API，獲取 MAPI 命名空間

    for account in mail_api.Accounts:
        # 遍歷所有郵箱帳戶

        print(f"  - Account Name: {account.DisplayName}")
        # 輸出帳戶名稱

        print(f"    Email Address: {account.SmtpAddress}")
        # 輸出郵箱地址

        print(f"    Store Path: {account.DeliveryStore.DisplayName}")
        # 輸出郵箱儲存路徑

        print()
        # 增加空行，使輸出更易於閱讀

    target_account = f_mail.mail_biaoti.find_outlook_account(
        mail_api,
        email_account,
    )
    # 查找目標郵箱帳戶

    folder = f_mail.mail_biaoti.get_folder_by_name(
        target_account,
        english_folder_name,
    )
    # 獲取指定名稱的郵箱資料夾

    emails = f_mail.mail_biaoti.get_emails(folder)
    # 獲取資料夾中的郵件列表

    f_mail.mail_biaoti.print_emails_in_folder(
        chinese_folder_name,
        emails,
    )
    # 輸出資料夾中的郵件資訊


# display_email_information()  # 調用函數，顯示郵件資訊