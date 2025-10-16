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


def clear_conditional_formatting(sheet):
    """
    清除指定工作表中的所有條件式格式設定。
    """
    try:
        sheet.Cells.FormatConditions.Delete()
        print("已清除所有條件式格式設定。")
    except Exception as e:
        print(f"清除條件式格式設定時發生錯誤: {e}")
        traceback.print_exc()


def apply_border_conditional_formatting(target_range, formula="=NOT(OR(A1=\"\",A1=0))"):
    """
    為指定的範圍加入條件式格式設定，並應用邊框樣式。
    """
    try:
        from win32com.client import constants
        if target_range.MergeCells:
            print("目標範圍包含合併儲存格，請確認並重試。")
            return

        format_condition = target_range.FormatConditions.Add(Type=constants.xlExpression, Formula1=formula)
        format_condition.SetFirstPriority()
        print(f"已加入條件式格式設定規則 (邊框)，公式: {formula}。")

        for border_type in [xlLeft, xlRight, xlTop, xlBottom]:
            border = format_condition.Borders(border_type)
            border.LineStyle = xlContinuous
            border.Weight = xlThin
        print("已為條件式格式設定規則應用邊框。")
    except Exception as e:
        print(f"應用邊框條件式格式設定時發生錯誤: {e}")
        traceback.print_exc()


def apply_font_conditional_formatting(target_range, formula="=OR(A1=\"\",A1=0)"):
    """
    為指定的範圍加入條件式格式設定，並應用字體顏色。
    """
    try:
        from win32com.client import constants
        if target_range.MergeCells:
            print("目標範圍包含合併儲存格，請確認並重試。")
            return

        format_condition = target_range.FormatConditions.Add(Type=constants.xlExpression, Formula1=formula)
        format_condition.SetFirstPriority()
        print(f"已加入條件式格式設定規則 (字體顏色)，公式: {formula}。")

        font = format_condition.Font
        font.ThemeColor = xlThemeColorDark1
        print("已為條件式格式設定規則應用字體顏色。")
    except Exception as e:
        print(f"應用字體顏色條件式格式設定時發生錯誤: {e}")
        traceback.print_exc()


def set_cell_value_and_select(sheet, value_cell="N12", value_to_set=0, select_cell="K7"):
    """
    設定指定儲存格的值，並選取另一個儲存格。
    """
    try:
        sheet.Range(value_cell).Value = value_to_set
        print(f"已將儲存格 {value_cell} 的值設定為 {value_to_set}。")
        sheet.Range(select_cell).Select()
        print(f"已選取儲存格 {select_cell}。")
    except Exception as e:
        print(f"設定儲存格值或選取儲存格時發生錯誤: {e}")
        traceback.print_exc()


def run_excel_conditional_formatting(target_range_address="A1:AA219"):
    """
    主函數，協調執行所有條件式格式設定操作。
    """
    excel_objects = initialize_excel()
    if not excel_objects:
        print("初始化失敗，程序終止。")
        sys.exit(1)

    excel, workbook, sheet = excel_objects
    try:
        clear_conditional_formatting(sheet)

        target_range = sheet.Range(target_range_address)
        print(f"目標範圍設定為: {target_range.Address}")

        apply_border_conditional_formatting(target_range)
        apply_font_conditional_formatting(target_range)

        set_cell_value_and_select(sheet)

        print("腳本執行成功。")
    except Exception as e:
        print(f"執行主操作時發生錯誤: {e}")
        traceback.print_exc()
    finally:
        try:
            pass
            #excel.Quit()
            pythoncom.CoUninitialize()
            print("Excel 已關閉，COM 已解除初始化。")
        except Exception as e:
            print(f"關閉 Excel 或解除初始化 COM 時發生錯誤: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    run_excel_conditional_formatting()