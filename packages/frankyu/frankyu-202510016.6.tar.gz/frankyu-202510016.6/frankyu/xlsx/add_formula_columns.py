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


def add_formula_columns(worksheet: win32.CDispatch, len_col: str = "K", count_col: str = "L", ref_col: str = "SN_NO",aaa = -7) -> None:
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
    worksheet.Range(f"{count_col}2").FormulaR1C1 = f"=COUNTIFS(C[{aaa}],[@[{ref_col}]])"
    # 沒有明確的返回值，函數完成其操作即可。