

def M90ShuNiuFenXi(bbb = "",path_yuanlai = r"U:\lori\Everex出貨資料\2025\5\Ecom\\",path = "U:\\lori\\Everex出貨資料\\2025\\5\\",time_="2025.05.13"):
    
    
    


    import f_excel.deepseek_python_20250427_416a78 as sn
    
    
    # -*- coding: utf-8 -*-
    
    
    import win32com.client as win32 # 導入win32com.client模組，用於與COM對象互動，通常用於Windows應用程式自動化，這裡用於控制Excel。
    import os # 導入os模組，用於作業系統相關操作，這裡用於檢查檔案是否存在。
    import traceback # 導入traceback模組，用於獲取詳細的錯誤堆疊資訊，方便除錯。
    from typing import Optional, Tuple # 從typing模組導入Optional和Tuple，用於提供類型提示，增強程式碼可讀性。
    
    # === 常量定義區 ===
    # 集中管理腳本中使用的各種設定值。
    DEFAULT_WORKBOOK_PATH = r"D:\3.xlsx" # 預設的工作簿檔案路徑。使用原始字串(r"...")避免反斜線的轉義問題。
    DEFAULT_SHEET_NAME = "B234-581" # 預設要複製的工作表名稱。
    DEFAULT_TABLE_NAME = "t1" # 預設創建的結構化表格(ListObject)的名稱。
    DEFAULT_PIVOT_NAME = "t3" # 預設創建的數據透視表的名稱。
    DEFAULT_DATE_STR = "2025.04.27" # 預設日期字串，程式碼中未使用，可能保留用於其他目的。
    XL_COUNT = -4112 # Excel內建常量，表示COUNT函數，用於數據透視表的值欄位匯總方式。這是通過COM介面訪問Excel功能時需要使用的特定值。
    XL_DATABASE = 1 # Excel內建常量，表示數據透視表數據源類型為數據庫或清單。
    XL_ROW_FIELD = 1 # Excel內建常量，表示將字段添加到數據透視表的行區域。
    
    
    def initialize_excel(visible: bool = True) -> win32.CDispatch:
    
        try:
            # 嘗試通過COM介面創建Excel應用程式實例。
            excel_app = win32.Dispatch("Excel.Application")
            # 設定Excel應用程式視窗是否可見。visible=True會彈出Excel視窗，False則在後台執行。
            excel_app.Visible = visible
            # 設定是否顯示警告訊息，如保存提示。False表示不顯示警告，靜默執行。
            excel_app.DisplayAlerts = False
            # 返回Excel應用程式COM對象。
            return excel_app
        except Exception as e:
            # 捕獲任何初始化過程中發生的異常。
            # 拋出一個RuntimeError，包含詳細錯誤信息，方便調用者處理。
            raise RuntimeError(f"Excel初始化失敗: {str(e)}")
    
    def open_workbook(excel_app: win32.CDispatch, file_path: str = DEFAULT_WORKBOOK_PATH, read_only: bool = False) -> win32.CDispatch:
    
        # 檢查檔案路徑是否存在，如果不存在則拋出FileNotFoundError。
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"工作簿文件不存在: {file_path}")
        try:
            # 調用Excel應用程式的Workbooks集合的Open方法打開指定檔案。
            # 第一個參數是檔案路徑。
            # 第二個參數 UpdateLinks (0): 不更新鏈接。
            # 第三個參數 ReadOnly (read_only): 根據參數決定是否只讀打開。
            # 第四個參數 Format (None): 自動判斷檔案格式。
            return excel_app.Workbooks.Open(file_path, 0, read_only, None)
        except Exception as e:
            # 捕獲打開工作簿過程中發生的異常。
            # 拋出一個RuntimeError，包含詳細錯誤信息。
            raise RuntimeError(f"打開工作簿失敗: {str(e)}")
    
    def copy_worksheet(workbook: win32.CDispatch, sheet_name: str = DEFAULT_SHEET_NAME, after_position: int = 1) -> win32.CDispatch:
    
        try:
            # 從工作簿的Sheets集合中獲取指定名稱的工作表。
            source_sheet = workbook.Sheets(sheet_name)
            # 調用源工作表的Copy方法。
            # After參數指定了新工作表將被放置在workbook.Sheets(after_position)之後。
            source_sheet.Copy(After=workbook.Sheets(after_position))
            # Copy操作成功後，新複製的工作表會自動成為當前活動的工作表，返回它。
            return workbook.ActiveSheet
        except Exception as e:
            # 捕獲工作表名稱錯誤（工作表不存在）或複製過程中的其他異常。
            # 拋出ValueError，包含詳細錯誤信息。
            raise ValueError(f"工作表'{sheet_name}'不存在或複製失敗: {str(e)}")
    
    
    def create_list_object(worksheet: win32.CDispatch, table_range: Optional[str] = None, table_name: str = DEFAULT_TABLE_NAME, has_headers: bool = True) -> win32.CDispatch:
    
        # worksheet.Parent 返回工作簿，工作簿的 Parent 返回 Excel 應用程式。
        excel_app = worksheet.Parent.Parent
        # 清除剪貼簿模式，這是一個良好的習慣，可以避免在某些Excel操作後出現異常。
        excel_app.CutCopyMode = False
        try:
            # 判斷是否指定了表格範圍。
            if table_range is None:
                # 如果沒有指定範圍，則使用A1單元格的CurrentRegion屬性獲取連續的數據區域作為表格範圍。
                data_range = worksheet.Range("A1").CurrentRegion
            else:
                # 如果指定了範圍字串，則使用該字串獲取Range對象。
                data_range = worksheet.Range(table_range)
    
            # 調用工作表的ListObjects集合的Add方法創建結構化表格。
            # SourceType=1 表示數據來源是 Excel 清單 (xlSrcRange)。
            # Source=data_range 指定表格的數據範圍（一個 Range 對象）。
            # XlListObjectHasHeaders=1 表示有標題行，2表示沒有標題行。
            table_obj = worksheet.ListObjects.Add(SourceType=1, Source=data_range, XlListObjectHasHeaders=1 if has_headers else 2)
            # 設定創建的結構化表格的名稱。
            table_obj.Name = table_name
            # 返回創建的表格COM對象。
            return table_obj
        except Exception as e:
            # 捕獲創建表格過程中發生的異常。
            # 拋出一個RuntimeError，包含詳細錯誤信息。
            raise RuntimeError(f"創建表格失敗: {str(e)}")
    
    def add_formula_columns(worksheet: win32.CDispatch, len_col: str = "K", count_col: str = "L", ref_col: str = "SN_NO") -> None:
    
        # 在K1單元格設置列標題為"len"。
        worksheet.Range(f"{len_col}1").Value = "len"
        # 在L1單元格設置列標題為"cou"。
        worksheet.Range(f"{count_col}1").Value = "cou"
        # 在K2單元格設置公式。FormulaR1C1使用R1C1引用樣式。
        # f"=LEN([@[{ref_col}]])" 是結構化表格中引用同一行 ref_col 列的值的公式。
        # Excel會自動將此公式應用於 len_col 列的每一行。
        worksheet.Range(f"{len_col}2").FormulaR1C1 = f"=LEN([@[{ref_col}]])"
        # 在L2單元格設置公式。
        # "=COUNTIFS(C[-7],[@[{ref_col}]])" 是使用COUNTIFS函數進行條件計數的公式。
        # C[-7] 表示相對於當前單元格 (count_col 列) 左邊第七列的整列。
        # [@[{ref_col}]] 引用同一行 ref_col 列的值作為計數條件。
        # 這個公式的目的是計算 ref_col 列的值在 C[-7] 列中出現的次數。
        # Excel會自動將此公式應用於 count_col 列的每一行。
        worksheet.Range(f"{count_col}2").FormulaR1C1 = f"=COUNTIFS(C[-7],[@[{ref_col}]])"
        # 沒有明確的返回值，函數完成其操作即可。
    
    
    
    def create_pivot_table(workbook: win32.CDispatch,
                           source_range: win32.CDispatch,  # 接收Range對象作為數據源
                           pivot_sheet_name: Optional[str] = None,
                           pivot_name: str = DEFAULT_PIVOT_NAME,
                           start_cell: str = "A3") -> Tuple[win32.CDispatch, win32.CDispatch]:
    
        try:
            # 在工作簿的末尾添加一個新的工作表。Sheets.Add() 返回新添加的工作表對象。
            new_sheet = workbook.Sheets.Add()
            # 如果指定了透視表工作表名稱，則嘗試重命名。
            if pivot_sheet_name:
                try:
                    # 設定新工作表的名稱。
                    new_sheet.Name = pivot_sheet_name
                except Exception as rename_error:
                    # 捕獲重命名失敗的異常（例如，名稱已存在或包含非法字元）。
                    print(f"警告: 工作表重命名失敗，使用默認名稱 ({str(rename_error)})")
    
            # 創建數據透視緩存 (PivotCache)。
            # SourceType=XL_DATABASE 表示數據源是 Excel 清單或數據庫範圍。
            # SourceData=source_range 直接傳入作為數據源的 Range 對象。
            pivot_cache = workbook.PivotCaches().Create(
                SourceType=XL_DATABASE,
                SourceData=source_range  # 直接使用Range對象作為數據源
            )
    
            # 創建數據透視表 (PivotTable)。
            # TableDestination 指定透視表放置的位置。這裡獲取新工作表上指定起始單元格的 Range 對象作為目標。
            destination_range = new_sheet.Range(start_cell)
            # TableName 設定透視表的名稱。
            pivot_table = pivot_cache.CreatePivotTable(
                TableDestination=destination_range,
                TableName=pivot_name
            )
    
            # 返回創建的數據透視表COM對象和新的工作表COM對象。
            return pivot_table, new_sheet
    
        except Exception as e:
            # 捕獲創建透視表過程中發生的任何異常。
            # 生成包含詳細錯誤信息和堆疊追蹤的字串。
            error_info = f"創建數據透視表失敗: {str(e)}\n詳細信息: {traceback.format_exc()}"
            # 打印錯誤信息。
            print(error_info)
            # 拋出RuntimeError，包含詳細錯誤信息。
            raise RuntimeError(error_info)
    
    
    def configure_pivot_fields(pivot_table: win32.CDispatch, row_fields: Tuple[str, ...] = ("cou", "len", "MODEL"), data_field: str = "SN_NO", data_function: int = XL_COUNT) -> None:
    
        # 設定是否顯示列總計。
        pivot_table.ColumnGrand = True
        # 設定是否顯示行總計。
        pivot_table.RowGrand = True
        # 設定是否應用自動格式。
        pivot_table.HasAutoFormat = True
    
        # 遍歷要設定為行標籤的字段列表。enumerate用於同時獲取索引(position)和字段名稱(field)。
        # position 從 1 開始計數，以符合 Excel COM 對象的 Position 屬性習慣。
        for position, field in enumerate(row_fields, start=1):
            try:
                # 獲取數據透視表中指定名稱的字段對象。
                pivot_field = pivot_table.PivotFields(field)
                # 設定字段的Orientation屬性為XL_ROW_FIELD，表示將其放到行標籤區域。
                pivot_field.Orientation = XL_ROW_FIELD
                # 設定字段在行標籤區域中的位置 (從1開始)。
                pivot_field.Position = position
            except Exception:
                # 如果獲取字段失敗（字段名稱可能在數據源中不存在），打印警告信息。
                print(f"警告: 字段'{field}'不存在")
    
        try:
            # 添加值字段。
            # Field參數指定要添加的字段對象。這裡通過名稱從 PivotFields 集合中獲取。
            # Name參數設定值字段在數據透視表中的顯示名稱，這裡設定為"計數項:原始字段名稱"。
            # Function參數設定匯總函數，這裡使用傳入的 data_function 進行匯總。
            pivot_table.AddDataField(Field=pivot_table.PivotFields(data_field), Name=f"計數項:{data_field}", Function=data_function)
        except Exception as e:
            # 捕獲添加值字段過程中可能發生的異常。
            print(f"警告: 添加值字段錯誤: {str(e)}")
    
        # 沒有明確的返回值，函數完成其操作即可。
    
    
    def cleanup_resources(excel_app: Optional[win32.CDispatch], workbook: Optional[win32.CDispatch]) -> None:
    
        # 使用try...finally塊確保即使在關閉或退出過程中發生錯誤，也能嘗試釋放COM對象。
        try:
            # 檢查工作簿對象是否存在。
            if workbook:
                # 如果存在，關閉工作簿。SaveChanges=True表示保存所有更改。
                # 如果不希望保存更改，可以設置為 False。
                workbook.Close(SaveChanges=True)
            # 檢查Excel應用程式對象是否存在。
            if excel_app:
                # 如果存在，退出Excel應用程式。
                excel_app.Quit()
        finally:
            # 這個塊總會執行。在這裡嘗試釋放COM對象。
            # 顯式地使用del關鍵字可以幫助Python的垃圾回收機制更早地釋放底層COM資源。
            if workbook:
                # 刪除工作簿對象的引用。
                del workbook
            if excel_app:
                # 刪除Excel應用程式對象的引用。
                del excel_app
    
    
    
    #import f_excel.d单函数.open_or_add_process_excel_with_r1c1 as op

    import frankyu.xlsx.active_excel_objects_get as ac
    
    
    app,bo,sh,rng = ac.active_excel_objects_get()
    
    sh2 = sn.copy_worksheet(bo,sheet_name=sh.Name)
    
    sh2.Name
    
    
    
    cjb =  sn.create_list_object(sh2)
    
    import  f_excel.d单函数.add_formula_columns as sn2
    
    
    
    
    
    
    
    sn2.add_formula_columns(sh2,len_col="H",count_col="I",ref_col="PCBSN",aaa=-6)
    
    
    
    bo.Name
    
    #snb,snsh = sn.create_pivot_table(workbook=bo,source_range=cjb)
    
    
    
    #sn.configure_pivot_fields(snb)
    
    def main():
    
        # 初始化 excel_app 和 workbook 變數為 None，以便在 finally 塊中安全檢查是否已成功創建它們。
        excel_app = None
        workbook = None
        try:
            # 第1步: 初始化Excel應用程式，設定為可見。
            print("正在初始化Excel應用程式...")
            excel_app = app
            print("Excel初始化成功。")
    
            # 第2步: 打開指定的工作簿。
            print(f"正在打開工作簿: {DEFAULT_WORKBOOK_PATH}")
            workbook = bo
            print("工作簿打開成功。")
    
            # 第3步: 複製源工作表。
            print(f"正在複製工作表: {DEFAULT_SHEET_NAME}")
            # 複製 DEFAULT_SHEET_NAME 指定的工作表，新工作表將放在第一個工作表之後。
            copied_sheet = sh2
            print(f"工作表複製成功，新工作表名稱: {copied_sheet.Name}")
    
            # 第4步: 在複製的工作表上創建結構化表格並獲取其範圍。
            print(f"正在創建結構化表格 '{DEFAULT_TABLE_NAME}'...")
            # 在 copied_sheet 上創建名稱為 DEFAULT_TABLE_NAME 的結構化表格。
            # 如果 table_range 為 None，函數將自動檢測 A1.CurrentRegion 作為範圍。
            table_obj = cjb  ####超级表
            # 獲取結構化表格的完整數據範圍 (包括標題行)，這個 Range 對象將作為數據透視表的數據源。
            source_range = table_obj.Range    ###超级表范围
            print(f"結構化表格創建成功，範圍: {source_range.Address}")
    
            # 第5步: 添加公式列。
            print("正在添加公式列...")
            # 在 copied_sheet 上添加 "len" 和 "cou" 列，公式基於 "SN_NO" 列。
            # 如果 copied_sheet 包含剛剛創建的結構化表格，這些公式將會自動填充到表格的每一行。
            #add_formula_columns(copied_sheet)
            print("公式列添加成功。")
    
            # 第6步: 創建數據透視表。
            print("正在創建數據透視表...")
            # 調用 create_pivot_table 函數，傳遞工作簿對象、結構化表格的 Range 對象作為數據源，並指定新透視表工作表名稱為 "分析報表"。
            pivot_table, pivot_sheet = create_pivot_table(      ####枢纽表     枢纽sheet
                workbook,
                source_range=source_range, # 使用結構化表格的 Range 對象作為數據源
                pivot_sheet_name="分析報表" # 指定新透視表工作表的名稱
            )
            print(f"數據透視表創建成功，位於工作表: {pivot_sheet.Name}")
    
            # 第7步: 配置數據透視表欄位。
            print("正在配置數據透視表欄位...")
            # 設定透視表的行標籤為 ("cou", "len", "MODEL")，值字段為 "SN_NO" 並使用計數匯總。
            configure_pivot_fields(pivot_table)
            print("數據透視表欄位配置成功。")
    
            # 第8步: 激活數據透視表所在的工作表，使其在Excel視窗中可見。
            print("正在激活透視表工作表...")
            pivot_sheet.Activate()
            print("透視表工作表激活成功。")
    
            # 第9步: 進行一些最終的格式優化。
            # 選取 A1 單元格。
            pivot_sheet.Range("A1").Select()
            # 取消凍結窗格 (如果在之前的操作中被凍結了)。
            excel_app.ActiveWindow.FreezePanes = False
            print("格式優化完成。")
    
            # 打印腳本執行成功的消息和結果保存位置。
            print(f"執行成功！結果保存在: {DEFAULT_WORKBOOK_PATH}")
    
        except Exception as e:
            # 捕獲整個流程中發生的任何未處理的異常。
            # 打印嚴重錯誤提示。
            print(f"⚠️ 嚴重錯誤: {str(e)}")
            # 打印詳細的錯誤堆疊追蹤，方便除錯。
            traceback.print_exc()
        finally:
            # 這個塊總會執行，用於清理資源。
            # 調用 cleanup_resources 函數關閉工作簿、退出Excel並釋放COM對象。
            print("正在清理資源...")
            #cleanup_resources(excel_app, workbook)
            print("資源清理完成。")
        return pivot_table, pivot_sheet
    
    
    shuNiuBiao,shuNiuSheet =main()
    
    
    
    import    f_excel.d单函数.shuniufenxi as snfx
    
    
    
    ###
    
    ### 选择对象  省略
    
    pivot_table_obj =snfx.select_pivot_table_and_field(sheet=shuNiuSheet,pivot_table_name=shuNiuBiao.Name,field_name="model")
    
    snfx.add_data_field_to_pivot_table(shuNiuBiao,data_field_name="PCBSN")
    
    snfx.copy_and_paste_range(shuNiuSheet)
    
    snfx.write_formula_to_cell(shuNiuSheet, "J6", "pcs")
    
    snfx.write_formula_to_cell(shuNiuSheet, "K6", time_)
    
    text_join_formula = '=TEXTJOIN(" ",,TRIM(H6),I6:L6)'
    
    
    
    
    snfx.write_formula_to_cell(shuNiuSheet, "K8", '=TEXTJOIN(" ",,TRIM(H6),I6:L6)')
    
    
    name_n = shuNiuSheet.Range("K8").Value
    name_n
    
    bo.Name

    name_full = path+name_n+".xlsx"
    import time
    time.sleep(5)

    #sh.Activate()  

    
    

    

    import os
    if os.path.isfile(name_full):
        import frankyu.frankyu as fr
        fr.gbc("excel")
        #app.Quit()
        #pass
    else:
        #pass

        sh.Activate()  
        
    
    
    
    
    
    
    
        bo.SaveAs(name_full)
        import time
        time.sleep(2)
        app.Quit()























#m90ShuNiuFenXi(list)

eee = r'''
if __name__ == "__main__":

    path = "U:\\lori\\Everex出貨資料\\2025\\5\\"
    
    path_yuanlai = r"U:\lori\Everex出貨資料\2025\5\M90\\"
    
    list_ = [r"U:\lori\Everex出貨資料\2025\5\M90\M90H 包裝掃描資料(第四批).xlsx",r"U:\lori\Everex出貨資料\2025\5\M90\M90S 包裝掃描資料(第十四批).xlsx"]
    
    
    bbb = "https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/xls/M90H%205120%20pcs%20%20%20%202025.05.13.xlsx"
    
    
    bbb = list_[1]
    
    
    for i in list_:
        m90ShuNiuFenXi(i)

'''   
if __name__ == "__main__":

    M90ShuNiuFenXi()