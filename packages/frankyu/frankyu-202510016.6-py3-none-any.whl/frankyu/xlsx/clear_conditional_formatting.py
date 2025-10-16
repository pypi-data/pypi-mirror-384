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