# -*- coding: utf-8 -*-
"""
Excel自動化處理腳本

功能架構：
1. 核心功能模組
    - 工作表複製
    - 結構化表格創建 (將數據範圍轉換為Excel Table)
    - 公式列添加 (在表格中新增列並填充公式)
    - 數據透視表生成 (基於表格數據創建數據透視表)
    - 數據後處理 (配置透視表欄位、格式化)

設計原則：
1. 模組化設計 - 每個功能獨立封裝成函數，提高可讀性和重用性。
2. 防禦式程式設計 - 包含檔案是否存在檢查、錯誤捕獲等，增強腳本的穩定性。
3. 資源管理 - 使用try...finally塊確保Excel應用程式和工作簿在執行完畢或出錯後能被正確關閉和釋放，避免資源洩漏。
4. 類型提示 (Type Hinting) - 使用Python的類型提示功能（如`: str`, `-> win32.CDispatch`），幫助理解函數預期接收和返回的數據類型，提高程式碼可讀性和可維護性。
5. 常量集中管理 - 將檔案路徑、工作表名稱、表格名稱等常用設定放在腳本開頭的常量區，方便修改和管理。

技術要點：
- 使用win32com庫實現Excel COM自動化，直接調用Excel應用程式的API來控制其行為。
- 完全模擬GUI操作流程 - win32com的操作邏輯很大程度上反映了在Excel使用者介面中的步驟（例如，創建PivotCache，然後基於Cache創建PivotTable）。
- 支援大範圍數據處理(13,900行) - COM自動化通常比直接讀寫檔案（如openpyxl, pandas）在處理特定複雜格式和操作（如透視表、結構化表格）時更具優勢，尤其適用於已經存在大量公式或特定格式的檔案。
- 自動化公式填充 - 利用Excel結構化表格的特性，在表格列中添加公式，該公式會自動應用於表格的所有行。
- 動態數據透視表配置 - 通過程式碼設定數據透視表的數據源、行列欄位和值欄位。

前置條件：
- 系統上安裝了Microsoft Excel。
- 安裝了Python環境。
- 安裝了win32com庫 (`pip install pywin32`)。

注意事項：
- COM自動化依賴於Excel的安裝，且可能會受到Excel版本差異的影響。
- 在腳本執行期間，Excel視窗可能會彈出（如果`visible=True`），請勿手動干擾。
- 處理大型檔案時，COM操作可能會比較耗時。
- 錯誤處理機制會嘗試捕獲COM錯誤，但某些底層COM異常可能需要更複雜的處理。
"""

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

# === 核心功能函數 ===

def initialize_excel(visible: bool = True) -> win32.CDispatch:
    """
    初始化並啟動Excel應用程式。

    Args:
        visible (bool, optional): 控制Excel應用程式視窗是否可見。
                                  - True: Excel視窗可見。
                                  - False: Excel在後台執行 (無GUI)。
                                  預設為 True。

    Returns:
        win32.CDispatch: 成功啟動的Excel應用程式的COM對象。

    Raises:
        RuntimeError: 如果Excel應用程式初始化失敗（例如，Excel未安裝或COM錯誤）。
    """
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
    """
    打開指定路徑的Excel工作簿。

    Args:
        excel_app (win32.CDispatch): 已初始化並運行的Excel應用程式的COM對象。
        file_path (str, optional): 要打開的工作簿檔案的完整路徑。
                                   預設使用常量 DEFAULT_WORKBOOK_PATH。
        read_only (bool, optional): 是否以只讀模式打開工作簿。
                                    - True: 以只讀模式打開。
                                    - False: 以讀寫模式打開。
                                    預設為 False。

    Returns:
        win32.CDispatch: 成功打開的工作簿的COM對象。

    Raises:
        FileNotFoundError: 如果指定路徑的檔案不存在。
        RuntimeError: 如果打開工作簿過程中發生其他錯誤。
    """
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
    """
    複製工作簿中的指定工作表，並將新工作表放在指定位置之後。

    Args:
        workbook (win32.CDispatch): Excel工作簿的COM對象。
        sheet_name (str, optional): 要複製的工作表的名稱。
                                    預設使用常量 DEFAULT_SHEET_NAME。
        after_position (int, optional): 指定複製後新工作表放置的位置。
                                        新工作表將被放在工作簿中索引為 `after_position` 的工作表之後。
                                        索引從 1 開始計算。
                                        預設為 1 (放在第一個工作表之後)。

    Returns:
        win32.CDispatch: 複製後的新工作表的COM對象。
                         複製操作成功後，新工作表會自動成為活動工作表 (ActiveSheet)。

    Raises:
        ValueError: 如果指定名稱的工作表不存在或複製過程中發生錯誤。
    """
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
    """
    在工作表上創建一個結構化表格 (ListObject)。

    Args:
        worksheet (win32.CDispatch): 要在其上創建表格的工作表的COM對象。
                                     假定此工作表上已存在數據。
        table_range (Optional[str], optional): 可選參數，指定表格的數據範圍，如"A1:C10"。
                                             如果為 None，函數將使用 `worksheet.Range("A1").CurrentRegion`
                                             自動檢測從 A1 單元格開始的連續數據區域。
                                             預設為 None。
        table_name (str, optional): 結構化表格的名稱。
                                    預設使用常量 DEFAULT_TABLE_NAME。
        has_headers (bool, optional): 指示數據範圍是否包含標題行。
                                      - True: 數據第一行是標題行。
                                      - False: 數據沒有標題行。
                                      預設為 True。

    Returns:
        win32.CDispatch: 成功創建的結構化表格 (ListObject) 的COM對象。

    Raises:
        RuntimeError: 如果創建表格過程中發生錯誤。
    """
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
    """
    在工作表中指定的列添加標題和公式。

    此函數通常用於在一個已經創建了結構化表格的工作表上添加計算列。
    由於是在結構化表格所在的列設置公式，Excel會自動將公式應用於表格的所有數據行。

    Args:
        worksheet (win32.CDispatch): 要添加列和公式的工作表的COM對象。
        len_col (str, optional): 用於存放長度計算公式的新列的列字母標識 (例如 "K")。
                                 預設為 "K"。
        count_col (str, optional): 用於存放計數計算公式的新列的列字母標識 (例如 "L")。
                                   預設為 "L"。
        ref_col (str, optional): 用於公式計算的參考列的標題名稱 (例如 "SN_NO")。
                                 預設為 "SN_NO"。

    Returns:
        None: 函數執行操作，沒有明確返回值。
    """
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


# 這個是第一個 create_pivot_table 函數定義，它使用了表格名稱字串作為數據源，
# 但在後面的 main 函數中未使用。保留但註釋掉，以防需要參考。
# def create_pivot_table(workbook: win32.CDispatch, source_table: str = DEFAULT_TABLE_NAME, pivot_sheet_name: Optional[str] = None, pivot_name: str = DEFAULT_PIVOT_NAME, start_cell: str = "A3") -> Tuple[win32.CDispatch, win32.CDispatch]:
#     try:
#         # 創建新工作表
#         new_sheet = workbook.Sheets.Add()
#         if pivot_sheet_name:
#             new_sheet.Name = pivot_sheet_name
#
#         # 偵錯訊息
#         print(f"偵錯: 數據源表格名稱 = {source_table}")
#         print(f"偵錯: 數據透視表目標位置 = {new_sheet.Name}!{start_cell}")
#
#         # 創建數據透視緩存
#         # SourceData 直接使用表格名稱字串
#         pivot_cache = workbook.PivotCaches().Create(SourceType=XL_DATABASE, SourceData=source_table)
#
#         # 偵錯訊息
#         print("偵錯: 數據透視緩存創建成功")
#
#         # 創建數據透視表
#         # TableDestination 使用工作表名稱和單元格地址字串
#         pivot_table = pivot_cache.CreatePivotTable(TableDestination=f"'{new_sheet.Name}'!{start_cell}", TableName=pivot_name)
#
#         # 偵錯訊息
#         print("偵錯: 數據透視表創建成功")
#         return pivot_table, new_sheet
#
#     except Exception as e:
#         print(f"創建數據透視表失敗，錯誤信息: {e.args}")
#         raise RuntimeError(f"創建數據透視表失敗: {str(e)}")


def create_pivot_table(workbook: win32.CDispatch,
                       source_range: win32.CDispatch,  # 接收Range對象作為數據源
                       pivot_sheet_name: Optional[str] = None,
                       pivot_name: str = DEFAULT_PIVOT_NAME,
                       start_cell: str = "A3") -> Tuple[win32.CDispatch, win32.CDispatch]:
    """
    創建一個新的工作表，並在其上創建一個數據透視表。

    此函數使用一個 Excel Range 對象作為數據透視表的數據源。

    Args:
        workbook (win32.CDispatch): 要在其中創建透視表的工作簿的COM對象。
        source_range (win32.CDispatch): 作為數據透視表數據源的 Range 對象。
                                       這通常是一個結構化表格的完整數據範圍 (包括標題)。
        pivot_sheet_name (Optional[str], optional): 可選參數，新創建的透視表工作表的名稱。
                                                    如果為 None，Excel 會給予一個預設名稱 (例如 "Sheet1", "Sheet2" 等)。
                                                    預設為 None。
        pivot_name (str, optional): 數據透視表的名稱。
                                    預設使用常量 DEFAULT_PIVOT_NAME。
        start_cell (str, optional): 數據透視表在目標工作表上的起始單元格地址 (例如 "A3")。
                                    預設為 "A3"。

    Returns:
        Tuple[win32.CDispatch, win32.CDispatch]: 一個包含兩個元素的元組：
                                                - 第一個元素是成功創建的數據透視表 (PivotTable) 的COM對象。
                                                - 第二個元素是包含數據透視表的新工作表 (Worksheet) 的COM對象。

    Raises:
        RuntimeError: 如果創建數據透視表過程中發生任何錯誤。
                      錯誤信息將包含詳細的 traceback。
    """
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
    """
    設定數據透視表的欄位布局（行標籤、值字段等）。

    Args:
        pivot_table (win32.CDispatch): 要配置的數據透視表的COM對象。
        row_fields (Tuple[str, ...], optional): 一個元組，包含要設置為行標籤的字段名稱。
                                               這些名稱必須與數據源中的列標題匹配。
                                               字段將按照元組中的順序添加到行區域。
                                               預設為 ("cou", "len", "MODEL")。
        data_field (str, optional): 用作值字段的字段名稱。
                                    這個字段的值將根據 data_function 進行匯總。
                                    預設為 "SN_NO"。
        data_function (int, optional): 值字段的匯總函數的 Excel 內建常量。
                                       例如，XL_COUNT (-4112) 表示計數。
                                       預設為 XL_COUNT。

    Returns:
        None: 函數執行操作，沒有明確返回值。
    """
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
    """
    安全地關閉工作簿和退出Excel應用程式，並釋放COM對象資源。

    此函數應在腳本執行結束（無論成功或失敗）時調用，以確保 Excel 進程正確終止。

    Args:
        excel_app (Optional[win32.CDispatch]): Excel應用程式的COM對象。
                                             如果應用程式未成功初始化，此參數可能為 None。
        workbook (Optional[win32.CDispatch]): Excel工作簿的COM對象。
                                            如果工作簿未成功打開，此參數可能為 None。

    Returns:
        None: 函數執行清理操作，沒有明確返回值。
    """
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

# === 主流程 ===
# 這個 main 函數是程式的入口點， orchestrates (協調) 調用上面的功能函數來完成整個自動化流程。
# 原始碼中存在兩個同名的 main 函數定義，Python 會執行後面的那個。
# 以下註釋針對實際被執行的第二個 main 函數進行詳細解釋。

# 這個是第一個 main 函數定義，由於後面有同名函數定義，此處的定義不會被執行到。
# 保留但註釋掉，以供參考。
# def main():
#     excel_app = None
#     workbook = None
#     try:
#         excel_app = initialize_excel(visible=True)
#         workbook = open_workbook(excel_app)
#         copied_sheet = copy_worksheet(workbook)
#         table_obj = create_list_object(copied_sheet) # 這裡創建表格，但獲取的 table_obj 在透視表創建時未使用
#         add_formula_columns(copied_sheet)
#         # 這裡調用第一個 create_pivot_table，它期望 source_table 是一個表格名稱字串
#         pivot_table, pivot_sheet = create_pivot_table(workbook)
#         configure_pivot_fields(pivot_table)
#         pivot_sheet.Activate()
#         print(f"腳本執行完成，結果保存在: {DEFAULT_WORKBOOK_PATH}")
#     except Exception as e:
#         print(f"⚠️ 腳本執行出錯: {str(e)}")
#         traceback.print_exc()
#     finally:
#         cleanup_resources(excel_app, workbook)

def main():
    """
    執行整個Excel自動化處理的主要流程。

    包括初始化Excel、打開工作簿、複製工作表、創建結構化表格、
    添加公式列、創建數據透視表、配置透視表欄位，以及清理資源。
    """
    # 初始化 excel_app 和 workbook 變數為 None，以便在 finally 塊中安全檢查是否已成功創建它們。
    excel_app = None
    workbook = None
    try:
        # 第1步: 初始化Excel應用程式，設定為可見。
        print("正在初始化Excel應用程式...")
        excel_app = initialize_excel(visible=True)
        print("Excel初始化成功。")

        # 第2步: 打開指定的工作簿。
        print(f"正在打開工作簿: {DEFAULT_WORKBOOK_PATH}")
        workbook = open_workbook(excel_app)
        print("工作簿打開成功。")

        # 第3步: 複製源工作表。
        print(f"正在複製工作表: {DEFAULT_SHEET_NAME}")
        # 複製 DEFAULT_SHEET_NAME 指定的工作表，新工作表將放在第一個工作表之後。
        copied_sheet = copy_worksheet(workbook)
        print(f"工作表複製成功，新工作表名稱: {copied_sheet.Name}")

        # 第4步: 在複製的工作表上創建結構化表格並獲取其範圍。
        print(f"正在創建結構化表格 '{DEFAULT_TABLE_NAME}'...")
        # 在 copied_sheet 上創建名稱為 DEFAULT_TABLE_NAME 的結構化表格。
        # 如果 table_range 為 None，函數將自動檢測 A1.CurrentRegion 作為範圍。
        table_obj = create_list_object(copied_sheet, table_name=DEFAULT_TABLE_NAME)
        # 獲取結構化表格的完整數據範圍 (包括標題行)，這個 Range 對象將作為數據透視表的數據源。
        source_range = table_obj.Range
        print(f"結構化表格創建成功，範圍: {source_range.Address}")

        # 第5步: 添加公式列。
        print("正在添加公式列...")
        # 在 copied_sheet 上添加 "len" 和 "cou" 列，公式基於 "SN_NO" 列。
        # 如果 copied_sheet 包含剛剛創建的結構化表格，這些公式將會自動填充到表格的每一行。
        add_formula_columns(copied_sheet)
        print("公式列添加成功。")

        # 第6步: 創建數據透視表。
        print("正在創建數據透視表...")
        # 調用 create_pivot_table 函數，傳遞工作簿對象、結構化表格的 Range 對象作為數據源，並指定新透視表工作表名稱為 "分析報表"。
        pivot_table, pivot_sheet = create_pivot_table(
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
        cleanup_resources(excel_app, workbook)
        print("資源清理完成。")

# 這是一個標準的Python慣用法，確保當腳本作為主程式執行時才調用 main() 函數。
# 如果腳本被作為模組導入到其他腳本中，__name__ 的值將不是 "__main__"，main() 函數就不會被自動執行。
if __name__ == "__main__":
    # 調用主流程函數開始執行腳本。
    main()