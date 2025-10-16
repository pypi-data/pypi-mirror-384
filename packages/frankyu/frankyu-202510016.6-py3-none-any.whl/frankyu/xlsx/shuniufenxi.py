import win32com.client as win32

def open_excel_and_select_sheet(filename="", sheet_name="Sheet1"):
    """
    打开 Excel 文件并选择指定的工作表 (Open Excel file and select the specified sheet).

    思路 (Thinking Process):
    1. 创建 Excel 应用程序对象 (Create an Excel application object).
    2. 如果提供了文件名，则打开该文件 (If a filename is provided, open the file). 否则，创建一个新的工作簿 (Otherwise, create a new workbook).
    3. 选择指定名称的工作表 (Select the sheet with the given name).

    Args:
        filename (str, optional): Excel 文件名 (Excel filename). Defaults to "".
        sheet_name (str, optional): 要选择的工作表名称 (Name of the sheet to select). Defaults to "Sheet1".

    Returns:
        tuple: 一个包含 Excel 应用程序对象和活动工作表对象的元组 (A tuple containing the Excel application object and the active worksheet object).
               如果发生错误，则返回 None, None (Returns None, None if an error occurs).
    """
    try:
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        if filename:
            workbook = excel.Workbooks.Open(filename)
        else:
            workbook = excel.Workbooks.Add()
        sheet = workbook.Sheets(sheet_name)
        excel.Visible = True  # 可选: 使 Excel 可见 (Optional: Make Excel visible)
        return excel, sheet
    except Exception as e:
        print(f"发生错误: {e}")  # An error occurred
        return None, None

def select_pivot_table_and_field(sheet, pivot_table_name="PivotTable1", field_name=""):
    """
    在指定工作表中选择透视表并选择特定的字段标签 (Select a pivot table in the specified sheet and select a specific field label).

    思路 (Thinking Process):
    1. 获取工作簿中指定名称的透视表对象 (Get the pivot table object with the specified name from the workbook).
    2. 使用 PivotSelect 方法选择指定的标签 (Use the PivotSelect method to select the specified label).

    Args:
        sheet: 活动工作表对象 (The active worksheet object).
        pivot_table_name (str, optional): 透视表的名称 (Name of the pivot table). Defaults to "PivotTable1".
        field_name (str, optional): 要选择的字段名称 (Name of the field to select). Defaults to "".

    Returns:
        object: 如果找到透视表则返回透视表对象，否则返回 None (Returns the pivot table object if found, otherwise returns None).
    """
    try:
        pivot_table = sheet.PivotTables(pivot_table_name)
        if field_name:
            pivot_table.PivotSelect(f"{field_name}[All]", win32.constants.xlLabelOnly + win32.constants.xlFirstRow, True)
        return pivot_table
    except Exception as e:
        print(f"无法找到透视表 '{pivot_table_name}': {e}")  # Could not find pivot table
        return None

def add_data_field_to_pivot_table(pivot_table, data_field_name, caption="Count of Data"):
    """
    向透视表中添加数据字段并设置其标题和计算方式为计数 (Add a data field to the pivot table and set its caption and calculation method to count).

    思路 (Thinking Process):
    1. 使用 AddDataField 方法将指定的字段添加到透视表的数据区域 (Use the AddDataField method to add the specified field to the data area of the pivot table).
    2. 设置新添加的数据字段的标题 (Set the caption of the newly added data field).
    3. 默认计算方式是计数 (The default calculation method is count).

    Args:
        pivot_table: 透视表对象 (The pivot table object).
        data_field_name (str): 要添加为数据字段的字段名称 (Name of the field to add as a data field).
        caption (str, optional): 数据字段的标题 (Caption of the data field). Defaults to "Count of Data".
    """
    try:
        pivot_table.AddDataField(pivot_table.PivotFields(data_field_name), caption, win32.constants.xlCount)
    except Exception as e:
        print(f"添加数据字段 '{data_field_name}' 失败: {e}")  # Failed to add data field

def copy_and_paste_range(sheet, copy_range="A1:J15", paste_range="H1"):
    """
    复制指定范围的单元格并将其粘贴到另一个范围 (Copy a specified range of cells and paste it to another range).

    思路 (Thinking Process):
    1. 选择要复制的单元格范围 (Select the range of cells to copy).
    2. 使用 Copy 方法复制选定的范围 (Use the Copy method to copy the selected range).
    3. 选择要粘贴的目标单元格 (Select the target cell for pasting).
    4. 使用 PasteSpecial 方法粘贴内容，格式设置为值和数字格式，并创建链接 (Use the PasteSpecial method to paste the content, with format set to values and number formats, and create a link).

    Args:
        sheet: 活动工作表对象 (The active worksheet object).
        copy_range (str, optional): 要复制的单元格范围 (Range of cells to copy). Defaults to "A1:J15".
        paste_range (str, optional): 要粘贴的目标单元格 (Target cell for pasting). Defaults to "H1".
    """
    try:
        sheet.Range(copy_range).Select()
        sheet.Range(copy_range.split(":")[1]).Activate() # 激活范围内的最后一个单元格 (Activate the last cell in the range)
        selection = sheet.Application.Selection
        selection.Copy()
        sheet.Range(paste_range).Select()
        sheet.PasteSpecial(Format=3, Link=1, DisplayAsIcon=False, IconFileName=False)
    except Exception as e:
        print(f"复制粘贴范围失败: {e}")  # Failed to copy and paste range

def write_formula_to_cell(sheet, cell, formula):
    """
    向指定单元格写入公式 (Write a formula to the specified cell).

    思路 (Thinking Process):
    1. 选择要写入公式的单元格 (Select the cell to write the formula to).
    2. 将指定的公式赋值给该单元格的 FormulaR1C1 属性 (Assign the specified formula to the FormulaR1C1 property of the cell).

    Args:
        sheet: 活动工作表对象 (The active worksheet object).
        cell (str): 要写入公式的单元格 (Cell to write the formula to).
        formula (str): 要写入的公式 (The formula to write).
    """
    try:
        sheet.Range(cell).Value = formula
        #sheet.ActiveCell.FormulaR1C1 = formula
    except Exception as e:
        print(f"写入公式 '{formula}' 到单元格 '{cell}' 失败: {e}")  # Failed to write formula to cell

def save_workbook(excel):
    """
    保存当前活动的工作簿 (Save the currently active workbook).

    思路 (Thinking Process):
    1. 使用活动工作簿对象的 Save 方法保存工作簿 (Use the Save method of the active workbook object to save the workbook).

    Args:
        excel: Excel 应用程序对象 (The Excel application object).
    """
    try:
        excel.ActiveWorkbook.Save()
        excel.Quit() # 关闭 Excel 应用程序 (Close the Excel application)
    except Exception as e:
        print(f"保存工作簿失败: {e}")  # Failed to save workbook

if __name__ == "__main__":
    excel_app, active_sheet = open_excel_and_select_sheet(sheet_name="だ猂厨")
    if excel_app and active_sheet:
        pivot_table_obj = select_pivot_table_and_field(active_sheet, pivot_table_name="t3", field_name="model")
        if pivot_table_obj:
            add_data_field_to_pivot_table(pivot_table_obj, data_field_name="PCBSN", caption="数量:PCBSN") # 数量:PCBSN (Quantity:PCBSN)
            copy_and_paste_range(active_sheet)
            write_formula_to_cell(active_sheet, "J6", "pcs")
            write_formula_to_cell(active_sheet, "K6", "2025.05.13")
            text_join_formula = '=TEXTJOIN(" ",,TRIM(R[-2]C[-3]),R[-2]C[-2]:R[-2]C[1])'
            write_formula_to_cell(active_sheet, "K8", text_join_formula)
            active_sheet.Range("K8").Copy()
            save_workbook(excel_app)