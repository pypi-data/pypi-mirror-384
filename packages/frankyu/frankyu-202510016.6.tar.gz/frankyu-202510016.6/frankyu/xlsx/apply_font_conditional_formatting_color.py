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


def apply_font_conditional_formatting(sheet,target_range_str="A1:AA999", formula="=OR(A1=\"\",A1=0)"):
    """
    為指定的範圍加入條件式格式設定，並應用字體顏色。
    """
    target_range = sheet.Range(target_range_str)
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


