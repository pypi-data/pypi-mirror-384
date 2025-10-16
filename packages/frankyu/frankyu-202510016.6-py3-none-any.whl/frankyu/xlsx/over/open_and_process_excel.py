import f_excel.create_new_excel_workbook as cr
import frankyu.frankyu as fr

def open_and_process_excel(file_url: str = r"https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/xls/72-101-D17103ET10-%20bom%20%20ASM%20%E9%9D%9E%E5%B8%B8%E9%87%8D%E8%A6%81%20_20250507183543380991.xlsx"):
    """
    打开指定的Excel文件并处理。
    
    参数:
        file_url (str): Excel文件的URL，默认为一个预设值。
        
    返回:
        tuple: (excel_app, workbook, first_sheet)，如果操作成功。
        None: 如果过程中发生错误。
    """
    description = "72-101-D17103ET10- bom  ASM 非常重要 _20250507183543380991"

    try:
        # 创建新的Excel实例
        excel_app, workbook_name, a = cr.create_new_excel_workbook(kill_existing_excel=True)
        
        try:
            # 尝试打开工作簿
            workbook = excel_app.Workbooks.Open(file_url)
            print(f"成功打开文件: {file_url}")
            
            try:
                # 获取第一个工作表
                first_sheet = workbook.Sheets(1)
                
                # 调用倒计时函数（假设是等待Excel加载）
                fr.countdown(10)

                # 成功完成所有操作，返回Excel应用、工作簿和第一个sheet
                return excel_app, workbook, first_sheet
                
            except Exception as e_sheet:
                print(f"[错误] 获取第一个Sheet或执行倒计时时出错: {e_sheet}")

        except Exception as e_open:
            print(f"[错误] 无法打开Excel文件: {file_url}\n错误信息: {e_open}")

    except ImportError as ie:
        print(f"[错误] 缺少必要的模块: {ie}")
    except Exception as e_general:
        print(f"[未知错误] 发生了一个意外错误: {e_general}")
    
    # 如果有任何错误发生，则返回None
    
    return None,None,None

# 调用函数
if __name__ == "__main__":
    result = open_and_process_excel()
    if result is not None:
        app, wb, sheet = result
        print("Excel应用程序实例、工作簿和第一个Sheet已成功获取")
        # 可以在这里对 sheet 做进一步操作
    else:
        print("未能成功获取Excel对象，请检查错误信息")