import win32com.client
import pythoncom
import sys
import traceback

# Excel 常數 (對應到 VBA 常數)
xlContinuous = 1
xlThin = 2
xlExpression = 1
xlLeft = 1
xlRight = 2
xlTop = 3
xlBottom = 4
xlThemeColorDark1 = 1


def initialize_excel(app_name="Excel.Application", visible=True):
    """
    初始化 Excel COM 物件，並返回 Excel 實例、工作簿和工作表。
    """
    try:
        pythoncom.CoInitialize()
        print("COM 已初始化。")

        try:
            # 嘗試獲取活動的 Excel 實例
            excel = win32com.client.GetActiveObject(app_name)
        except pythoncom.com_error:
            # 如果沒有活動的實例，啟動一個新實例
            print(f"無法找到活動的 {app_name} 實例，啟動新實例。")
            excel = win32com.client.Dispatch(app_name)

        # 確保 Excel 被正確啟動
        if excel is None:
            print(f"無法啟動或訪問 {app_name} 應用程序。")
            return None

        # 設置 Excel 為前台顯示並取消提醒
        excel.Visible = visible
        excel.DisplayAlerts = False
        print("Excel 已設置為前台顯示，並取消提醒。")

        try:
            # 嘗試獲取活動工作簿
            workbook = excel.ActiveWorkbook
            if workbook is None:
                print("沒有活動的工作簿，創建一個新工作簿。")
                workbook = excel.Workbooks.Add()
        except Exception as e:
            print(f"取得活動工作簿時發生錯誤: {e}")
            traceback.print_exc()
            return None

        try:
            # 嘗試獲取活動工作表
            sheet = workbook.ActiveSheet
            if sheet is None:
                print("沒有活動的工作表，請確認工作簿包含有效的工作表。")
                return None
        except Exception as e:
            print(f"取得活動工作表時發生錯誤: {e}")
            traceback.print_exc()
            return None

        print("Excel 初始化成功。")
        return excel, workbook, sheet

    except Exception as e:
        print(f"初始化過程中發生未知錯誤: {e}")
        traceback.print_exc()
        return None