import win32com.client
import time

def active_excel_objects_get(excel_application=None):
    """
    获取或创建Excel应用程序、活动工作簿、活动工作表和A1单元格
    
    Args:
        excel_application: 可选，已有的Excel应用程序对象
        
    Returns:
        元组 (excel_app, workbook, worksheet, range_A1)
            excel_app: Excel应用程序对象
            workbook: 活动工作簿对象
            worksheet: 活动工作表对象
            range_A1: 活动工作表的A1单元格对象
        
    Raises:
        Exception: 当无法初始化Excel对象时抛出
    """
    try:
        # 处理Excel应用程序
        if excel_application is None:
            try:
                excel_application = win32com.client.GetObject(None, "Excel.Application")
                print("已连接到现有Excel应用程序")
                print(f"当前警告显示状态: {'开启' if excel_application.DisplayAlerts else '关闭'}")
                #print(f"是否可以强制关闭: {'是' if excel_application.EnableCancelKey else '否'}")
            except:
                excel_application = win32com.client.Dispatch("Excel.Application")
                excel_application.Visible = True
                excel_application.DisplayAlerts = False
                print("已创建新Excel应用程序")
                print(f"警告显示状态设置为: {'开启' if excel_application.DisplayAlerts else '关闭'}")
                print(f"是否可以强制关闭: {'是' if excel_application.EnableCancelKey else '否'}")
        
        # 确保Excel应用程序有效
        if excel_application is None:
            raise Exception("无法创建或获取Excel应用程序实例")
            
        # 处理工作簿
        try:
            active_workbook = excel_application.ActiveWorkbook
            if active_workbook is None:
                active_workbook = excel_application.Workbooks.Add()
                print(f"已创建新工作簿: {active_workbook.Name}")
            else:
                print(f"已获取现有工作簿: {active_workbook.Name}")
        except Exception as e:
            active_workbook = excel_application.Workbooks.Add()
            print(f"异常后创建新工作簿: {active_workbook.Name}")
            
        # 处理工作表
        try:
            active_worksheet = active_workbook.ActiveSheet
            if active_worksheet is None:
                active_worksheet = active_workbook.Sheets.Add()
                print(f"已创建新工作表: {active_worksheet.Name}")
            else:
                print(f"已获取现有工作表: {active_worksheet.Name}")
        except Exception as e:
            active_worksheet = active_workbook.Sheets.Add()
            print(f"异常后创建新工作表: {active_worksheet.Name}")
            
        # 获取A1单元格
        first_cell = active_worksheet.Range("A1")
        print(f"已获取单元格: {first_cell.Address}")
        
        # 打印返回值的详细描述
        print("\n返回值描述:")
        print(f"1. Excel应用程序对象: {excel_application}")
        print(f"   版本: {excel_application.Version}")
        print(f"   可见性: {'可见' if excel_application.Visible else '不可见'}")
        print(f"   警告显示状态: {'开启' if excel_application.DisplayAlerts else '关闭'}")
        #print(f"   是否可以强制关闭: {'是' if excel_application.EnableCancelKey else '否'}")
        
        print(f"\n2. 工作簿对象: {active_workbook}")
        print(f"   名称: {active_workbook.Name}")
        print(f"   路径: {active_workbook.Path if active_workbook.Path else '未保存'}")
        print(f"   完整名称:  {active_workbook.Path}/{active_workbook.Name}")
        print(f"   工作表数量: {active_workbook.Sheets.Count}")
        
        print(f"\n3. 工作表对象: {active_worksheet}")
        print(f"   名称: {active_worksheet.Name}")
        print(f"   索引: {active_worksheet.Index}")
        print(f"   使用范围: {active_worksheet.UsedRange.Address if active_worksheet.UsedRange else '无数据'}")
        
        print(f"\n4. 单元格对象: {first_cell}")
        print(f"   地址: {first_cell.Address}")
        print(f"   值: {first_cell.Value if first_cell.Value is not None else '空'}")
        print(f"   行号: {first_cell.Row}, 列号: {first_cell.Column}")
        
        return excel_application, active_workbook, active_worksheet, first_cell
        
    except Exception as e:
        raise Exception(f"Excel对象初始化失败: {str(e)}")


if __name__ == "__main__":
    try:
        excel_app, workbook, worksheet, cell = active_excel_objects_get()
        cell.Value = 1234
        print(f"\n操作结果: 已在单元格 {cell.Address} 设置值: {cell.Value}")
        time.sleep(10)
    except Exception as e:
        print(f"操作失败: {e}")