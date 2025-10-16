import frankyu.xlsx.active_excel_objects_get_2 as ac

def url(file_path: str=r'https://d.docs.live.net/380c326fa2fd9c70/%E7%A7%81%E4%BA%BA%E6%96%87%E4%BB%B6%EF%BC%8Cdengchunying1988/%E6%A1%8C%E9%9D%A2%201/%E5%AD%A6%E4%B9%A0/%E5%AE%B6%E5%BA%AD%E8%B4%A6%E7%B0%BF%E6%9B%B4%E6%96%B0%E4%BA%8E2025%E5%B9%B43%E6%9C%8812%E6%97%A5.xlsx'
, file_name: str='家庭账簿更新于2025年3月12日.xlsx'):
    """
    Opens an Excel workbook. If the workbook is already open, it prints a message.
    Otherwise, it opens the workbook from the given path.

    Args:
        file_path (str): The full path to the Excel file.
        file_name (str): The name of the Excel file (e.g., "my_workbook.xlsx").
    """
    app, b, c, d = ac.active_excel_objects_get()

    workbook_found = False
    for workbook in app.Workbooks:
        if workbook.Name == file_name:
            print(f"'{file_name}' 已经打开")
            workbook_found = True
            break

    if not workbook_found:
        app.Workbooks.Open(file_path)
        print(f"'{file_name}' 已经打开") # Added this line for clarity after opening

if __name__ == "__main__":
    url()