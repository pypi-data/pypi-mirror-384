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


def set_cell_value_and_select(sheet, value_cell="A1", value_to_set=1, select_cell="A2"):
    """
    設定指定儲存格的值，並選取另一個儲存格。
    """
    
    try:
        sheet.Range("A3").Select()
        sheet.Range(value_cell).Value = value_to_set
        print(f"已將儲存格 {value_cell} 的值設定為 {value_to_set}。")
        if select_cell:
            
            sheet.Range(select_cell).Select()
            
        print(f"已選取儲存格 {select_cell}。")
    except Exception as e:
        print(f"設定儲存格值或選取儲存格時發生錯誤: {e}")
        traceback.print_exc()
