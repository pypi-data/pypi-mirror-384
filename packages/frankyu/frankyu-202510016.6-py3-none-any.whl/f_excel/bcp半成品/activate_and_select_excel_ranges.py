import win32com.client as win32

def activate_and_select_excel_ranges(
    target_sheet_index=2,
    selection_range="A1:A10",
    activation_range="C1:C10",
    show_excel=True,
    cleanup=True
):
    """
    安全地在Excel中激活和选择单元格区域的增强版本
    
    参数:
        target_sheet_index (int): 目标工作表索引(1-based)
        selection_range (str): 要选择的区域地址
        activation_range (str): 要激活的区域地址
        show_excel (bool): 是否显示Excel窗口
        cleanup (bool): 是否自动清理资源
        
    返回:
        tuple: (excel_app, workbook, worksheet) 对象
    """
    excel = None
    workbook = None
    worksheet = None
    
    try:
        # 初始化Excel
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        excel.Visible = show_excel
        excel.ScreenUpdating = show_excel
        
        # 创建新工作簿
        workbook = excel.Workbooks.Add()
        
        # 确保目标工作表存在
        while workbook.Worksheets.Count < target_sheet_index:
            new_sheet = workbook.Worksheets.Add()
            print(f"已添加工作表: {new_sheet.Name}")
        
        # 获取目标工作表
        worksheet = workbook.Worksheets(target_sheet_index)        # 获取目标工作表
        worksheet2 = workbook.Worksheets(target_sheet_index-1) 
        worksheet2.Range("A1").Value= 1
        
        
        # 确保工作表可用
        if worksheet.Visible != win32.constants.xlSheetVisible:
            worksheet.Visible = win32.constants.xlSheetVisible
        
        # 准备操作区域
        def safe_get_range(range_address):
            try:
                return worksheet.Range(range_address)
            except:
                print(f"无效的区域地址: {range_address}")
                return None
        
        range_to_select = safe_get_range(selection_range)
        range_to_activate = safe_get_range(activation_range)
        
        # 解除工作表保护
        if worksheet.ProtectContents:
            try:
                worksheet.Unprotect()
                print("已解除工作表保护")
            except Exception as e:
                print(f"解除保护失败: {e}")
        
        # 确保退出编辑模式
        excel.SendKeys("{ESC}")
        
        # 尝试选择区域
        if range_to_select:
            try:
                worksheet2.Application.Goto(range_to_select, Scroll=True)
                print(f"已滚动到区域: {selection_range}")
            except Exception as e:
                print(f"区域选择失败: {e}")
        
        # 尝试激活区域
        if range_to_activate:
            try:
                worksheet.Application.Goto(
                    range_to_activate.Cells(1, 1), 
                    Scroll=True
                )
                print(f"已激活区域: {activation_range}")
            except Exception as e:
                print(f"区域激活失败: {e}")
        
        return excel, workbook, worksheet
        
    except Exception as e:
        print(f"操作失败: {e}")
        if excel and cleanup:
            try:
                if workbook:
                    workbook.Close(False)
                excel.Quit()
            except:
                pass
        raise
        
    finally:
        if cleanup and excel:
            try:
                if workbook:
                    workbook.Close(False)
                excel.Quit()
            except:
                pass

# 使用示例
if __name__ == "__main__":
    try:
        # 示例用法
        excel_app, wb, ws = activate_and_select_excel_ranges(
            target_sheet_index=5,
            selection_range="B2:D5",
            activation_range="F1:H3",
            cleanup=False
        )
        
        # 继续操作
        if ws:
            ws.Range("A1").Value = "操作成功"
            input("按Enter退出...")
        
    except Exception as e:
        print(f"执行错误: {e}")
    finally:
        if 'excel_app' in locals():
            excel_app.Quit()