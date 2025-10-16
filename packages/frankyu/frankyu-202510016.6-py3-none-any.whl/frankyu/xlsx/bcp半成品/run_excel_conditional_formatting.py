import win32com.client  # 导入
import pythoncom  # 导入
import sys  # 导入
import traceback  # 追溯

# Excel 常數 (constant) (對應 (correspond)
# 到 VBA 常數)
xlContinuous = 1  # xlContinuous (連續的)
xlThin = 2  # xlThin (細的)
xlExpression = 1  # xlExpression (表達式)
xlLeft = 1  # xlLeft (左)
xlRight = 2  # xlRight (右)
xlTop = 3  # xlTop (頂部/上)
xlBottom = 4  # xlBottom (底部/下)
xlThemeColorDark1 = 1  # xlThemeColorDark1 (主題顏色深 1)


def initialize_excel(  # 定義函數 (function) 初始化 (initialize)
    # Excel
    app_name="Excel.Application",  # app_name: 指定要連接或
    # 啟動的 Excel 應用程式的名稱，預設為 "Excel.Application"。
    visible=True  # visible: 一個布林值，指示 Excel
    # 應用程式是否應該在啟動時可見，預設為 True。
):
    """
    初始化 (initialize) Excel COM 物件 (object)，並返回 (return)
    Excel 實例 (instance)、工作簿 (workbook) 和工作表 (worksheet)。
    """
    # 思路:
    # 1. 嘗試初始化 COM 元件 (pythoncom.CoInitialize)。
    # 2. 嘗試獲取一個正在運行的 Excel 應用程式實例
    #    (win32com.client.GetActiveObject)。
    # 3. 如果沒有正在運行的實例，則啟動一個新的 Excel
    #    應用程式實例 (win32com.client.Dispatch)。
    # 4. 檢查 Excel 實例是否成功獲取或啟動。
    # 5. 設置 Excel 應用程式的可見性並禁用警告提示。
    # 6. 嘗試獲取活動的工作簿 (excel.ActiveWorkbook)。
    #    如果沒有活動的工作簿，則創建一個新的工作簿。
    # 7. 嘗試獲取活動的工作表 (workbook.ActiveSheet)。
    # 8. 如果所有步驟都成功，則返回 Excel 應用程式實例、
    #    工作簿和工作表。
    # 9. 在任何步驟中如果發生錯誤，則打印錯誤信息並返回 None。
    try:
        pythoncom.CoInitialize()  # 初始化 (initialize) COM
        print("COM 已初始化 (initialized)。")  # 打印

        try:
            # 嘗試 (try) 獲取 (get) 活動 (active) 的 Excel
            # 實例 (instance)
            excel = win32com.client.GetActiveObject(app_name)
            # 獲取活動對象 (get active object)
        except pythoncom.com_error:  # 捕捉 (catch) COM 錯誤 (error)
            # 如果 (if) 沒有 (no) 活動 (active) 的實例
            # (instance)，啟動 (launch) 一個新 (new) 實例 (instance)
            print(
                f"無法 (cannot) 找到 (find) 活動 (active) 的 "
                f"{app_name} 實例 (instance)，啟動 (launch) 新 (new) "
                f"實例 (instance)。"
            )  # 打印
            excel = win32com.client.Dispatch(app_name)
            # 創建對象 (create object)

        # 確保 (ensure) Excel 被 (be) 正確地 (correctly)
        # 啟動 (launched)
        if excel is None:  # 如果 (if) excel 是 None
            print(
                f"無法 (cannot) 啟動 (launch) 或 (or) 訪問 (access) "
                f"{app_name} 應用程序 (application)。"
            )  # 打印
            return None  # 返回 (return) None

        # 設置 (set) Excel 為 (to) 前台 (foreground) 顯示
        # (display) 並 (and) 取消 (cancel) 提醒 (alerts)
        excel.Visible = visible  # 可見性 (visibility)
        excel.DisplayAlerts = False  # 顯示警告 (display alerts)
        print("Excel 已設置 (set) 為 (to) 前台 (foreground) 顯示 "
              "(display)，並 (and) 取消 (canceled) 提醒 (alerts)。")  # 打印

        try:
            # 嘗試 (try) 獲取 (get) 活動 (active) 工作簿 (workbook)
            workbook = excel.ActiveWorkbook  # 活動工作簿 (active workbook)
            if workbook is None:  # 如果 (if) workbook 是 None
                print("沒有 (no) 活動 (active) 的工作簿 (workbook)，"
                      "創建 (create) 一個新 (new) 工作簿 (workbook)。")  # 打印
                workbook = excel.Workbooks.Add()  # 添加工作簿 (add workbook)
        except Exception as e:  # 捕捉 (catch) 異常 (exception)
            print(
                f"取得 (get) 活動 (active) 工作簿 (workbook) 時 "
                f"(when) 發生 (occurred) 錯誤 (error): {e}"
            )  # 打印
            traceback.print_exc()  # 打印異常信息 (print exception information)
            return None  # 返回 (return) None

        try:
            # 嘗試 (try) 獲取 (get) 活動 (active) 工作表
            # (worksheet)
            sheet = workbook.ActiveSheet  # 活動工作表 (active worksheet)
            if sheet is None:  # 如果 (if) sheet 是 None
                print(
                    "沒有 (no) 活動 (active) 的工作表 (worksheet)，請 (please) "
                    "確認 (confirm) 工作簿 (workbook) 包含 (contains) "
                    "有效 (valid) 的工作表 (worksheet)。"
                )  # 打印
                return None  # 返回 (return) None
        except Exception as e:  # 捕捉 (catch) 異常 (exception)
            print(
                f"取得 (get) 活動 (active) 工作表 (worksheet) 時 "
                f"(when) 發生 (occurred) 錯誤 (error): {e}"
            )  # 打印
            traceback.print_exc()  # 打印異常信息 (print exception information)
            return None  # 返回 (return) None

        print("Excel 初始化 (initialized) 成功 (successfully)。")  # 打印
        return excel, workbook, sheet  # 返回 (return)

    except Exception as e:  # 捕捉 (catch) 異常 (exception)
        print(
            f"初始化 (initialization) 過程中 (process) 發生 (occurred) "
            f"未知 (unknown) 錯誤 (error): {e}"
        )  # 打印
        traceback.print_exc()  # 打印異常信息 (print exception information)
        return None  # 返回 (return) None


def clear_conditional_formatting(  # 定義函數 (function) 清除 (clear)
    # 條件式格式設定 (conditional formatting)
    sheet  # sheet: 要清除條件式格式設定的工作表物件。
):
    """
    清除 (clear) 指定 (specified) 工作表 (worksheet) 中的 (in) 所有
    (all) 條件式格式設定 (conditional formatting)。
    """
    # 思路:
    # 1. 使用傳入的工作表物件 (sheet)。
    # 2. 訪問工作表中的所有單元格 (sheet.Cells)。
    # 3. 訪問單元格的格式條件集合 (.FormatConditions)。
    # 4. 調用集合的 Delete 方法來移除所有條件式格式設定。
    # 5. 如果操作成功，則打印成功的消息。
    # 6. 如果發生任何異常，則捕獲異常，打印錯誤消息和異常追溯信息。
    try:
        sheet.Cells.FormatConditions.Delete()  # 刪除 (delete) 格式條件
        # (format conditions)
        print("已清除 (cleared) 所有 (all) 條件式格式設定 "
              "(conditional formatting)。")  # 打印
    except Exception as e:  # 捕捉 (catch) 異常 (exception)
        print(
            f"清除 (clearing) 條件式格式設定 (conditional "
            f"formatting) 時 (when) 發生 (occurred) 錯誤 (error): {e}"
        )  # 打印
        traceback.print_exc()  # 打印異常信息 (print exception information)


def apply_border_conditional_formatting(  # 定義函數 (function) 應用 (apply)
    # 邊框 (border) 條件式格式設定 (conditional formatting)
    target_range,  # target_range: 要應用條件式格式設定的 Excel
    # 範圍物件。
    formula="=NOT(OR(A1=\"\",A1=0))"  # formula: 用於判斷是否應用邊框的
    # Excel 公式，預設為 "=NOT(OR(A1=\"\",A1=0))"，表示當 A1 不為空且不為 0 時應用邊框。
):
    """
    為 (for) 指定 (specified) 的範圍 (range) 加入 (add) 條件式格式設定
    (conditional formatting)，並 (and) 應用 (apply) 邊框樣式 (border style)。
    """
    # 思路:
    # 1. 從 win32com.client 導入 constants 以使用 Excel 常量。
    # 2. 檢查目標範圍是否包含合併的單元格，如果是則打印消息並返回，
    #    因為在合併的單元格上應用條件式格式設定可能會導致問題。
    # 3. 使用目標範圍的 FormatConditions.Add 方法添加一個新的條件式
    #    格式設定規則，類型設置為基於公式 (xlExpression)，公式使用傳入的 formula。
    # 4. 將新創建的格式條件設置為第一個優先級。
    # 5. 遍歷邊框的四個邊 (左、右、上、下)。
    # 6. 對於每個邊，獲取其邊框物件，並設置線條樣式為連續 (xlContinuous)
    #    和粗細為細 (xlThin)。
    # 7. 如果操作成功，則打印成功的消息。
    # 8. 如果發生任何異常，則捕獲異常，打印錯誤消息和異常追溯信息。
    try:
        from win32com.client import constants  # 從 (from) win32com.client
        # 導入 (import) 常數 (constants)
        if target_range.MergeCells:  # 如果 (if) 目標範圍 (target range)
            # 包含合併儲存格 (merge cells)
            print(
                "目標範圍 (target range) 包含 (contains) 合併儲存格 "
                "(merged cells)，請 (please) 確認 (confirm) 並 (and) "
                "重試 (retry)。"
            )  # 打印
            return  # 返回 (return)

        format_condition = target_range.FormatConditions.Add(  # 添加 (add)
            # 格式條件 (format condition)
            Type=constants.xlExpression,  # Type: 條件式格式設定的類型，
            # 此處使用 xlExpression 表示基於公式。
            Formula1=formula  # Formula1: 條件式格式設定的公式。
        )
        format_condition.SetFirstPriority()  # 設置 (set) 首要 (first)
        # 優先級 (priority)
        print(
            f"已加入 (added) 條件式格式設定 (conditional "
            f"formatting) 規則 (rule) (邊框 (border))，公式 (formula): "
            f"{formula}。"
        )  # 打印

        for border_type in [xlLeft, xlRight, xlTop, xlBottom]:  # 遍歷
            # (iterate) 邊框類型 (border type)
            border = format_condition.Borders(border_type)
            # border_type: 指定要設定邊框的邊，可以是 xlLeft、xlRight、
            # xlTop 或 xlBottom。
            border.LineStyle = xlContinuous  # LineStyle: 邊框的線條樣式，
            # 此處使用 xlContinuous 表示實線。
            border.Weight = xlThin  # Weight: 邊框的粗細，此處使用 xlThin
            # 表示細線。
        print("已為 (for) 條件式格式設定 (conditional formatting) 規則 "
              "(rule) 應用 (applied) 邊框 (border)。")  # 打印
    except Exception as e:  # 捕捉 (catch) 異常 (exception)
        print(
            f"應用 (applying) 邊框 (border) 條件式格式設定 "
            f"(conditional formatting) 時 (when) 發生 (occurred) 錯誤 "
            f"(error): {e}"
        )  # 打印
        traceback.print_exc()  # 打印異常信息 (print exception information)


def apply_font_conditional_formatting(  # 定義函數 (function) 應用 (apply)
    # 字體 (font) 條件式格式設定 (conditional formatting)
    target_range,  # target_range: 要應用條件式格式設定的 Excel
    # 範圍物件。
    formula="=OR(A1=\"\",A1=0)"  # formula: 用於判斷是否應用字體格式的
    # Excel 公式，預設為 "=OR(A1=\"\",A1=0)"，表示當 A1 為空或為 0 時應用字體格式。
):
    """
    為 (for) 指定 (specified) 的範圍 (range) 加入 (add) 條件式格式設定
    (conditional formatting)，並 (and) 應用 (apply) 字體顏色 (font color)。
    """
    # 思路:
    # 1. 從 win32com.client 導入 constants 以使用 Excel 常量。
    # 2. 檢查目標範圍是否包含合併的單元格，如果是則打印消息並返回，
    #    因為在合併的單元格上應用條件式格式設定可能會導致問題。
    # 3. 使用目標範圍的 FormatConditions.Add 方法添加一個新的條件式
    #    格式設定規則，類型設置為基於公式 (xlExpression)，公式使用傳入的 formula。
    # 4. 將新創建的格式條件設置為第一個優先級。
    # 5. 獲取格式條件的字體物件。
    # 6. 設置字體的顏色為主題顏色 Dark1 (xlThemeColorDark1)。
    # 7. 如果操作成功，則打印成功的消息。
    # 8. 如果發生任何異常，則捕獲異常，打印錯誤消息和異常追溯信息。
    try:
        from win32com.client import constants  # 從 (from) win32com.client
        # 導入 (import) 常數 (constants)
        if target_range.MergeCells:  # 如果 (if) 目標範圍 (target range)
            # 包含合併儲存格 (merge cells)
            print(
                "目標範圍 (target range) 包含 (contains) 合併儲存格 "
                "(merged cells)，請 (please) 確認 (confirm) 並 (and) "
                "重試 (retry)。"
            )  # 打印
            return  # 返回 (return)

        format_condition = target_range.FormatConditions.Add(  # 添加 (add)
            # 格式條件 (format condition)
            Type=constants.xlExpression,  # Type: 條件式格式設定的類型，
            # 此處使用 xlExpression 表示基於公式。
            Formula1=formula  # Formula1: 條件式格式設定的公式。
        )
        format_condition.SetFirstPriority()  # 設置 (set) 首要 (first)
        # 優先級 (priority)
        print(
            f"已加入 (added) 條件式格式設定 (conditional "
            f"formatting) 規則 (rule) (字體顏色 (font color))，公式 "
            f"(formula): {formula}。"
        )  # 打印

        font = format_condition.Font  # 字體 (font)
        font.ThemeColor = xlThemeColorDark1  # ThemeColor: 字體的顏色，
        # 此處使用主題顏色 Dark1。
        print("已為 (for) 條件式格式設定 (conditional formatting) 規則 "
              "(rule) 應用 (applied) 字體顏色 (font color)。")  # 打印
    except Exception as e:  # 捕捉 (catch) 異常 (exception)
        print(
            f"應用 (applying) 字體顏色 (font color) 條件式格式設定 "
            f"(conditional formatting) 時 (when) 發生 (occurred) 錯誤 "
            f"(error): {e}"
        )  # 打印
        traceback.print_exc()  # 打印異常信息 (print exception information)


def set_cell_value_and_select(  # 定義函數 (function) 設置 (set) 儲存格值
    # (cell value) 並 (and) 選取 (select)
    sheet,  # sheet: 要操作的工作表物件。
    value_cell="N12",  # value_cell: 要設定值的目標儲存格地址，
    # 預設為 "N12"。
    value_to_set=0,  # value_to_set: 要設定到目標儲存格的值，
    # 預設為 0。
    select_cell="K7"  # select_cell: 設定值後要選取的儲存格地址，
    # 預設為 "K7"。
):
    """
    設定 (set) 指定 (specified) 儲存格 (cell) 的值 (value)，並 (and)
    選取 (select) 另一個 (another) 儲存格 (cell)。
    """
    # 思路:
    # 1. 使用傳入的工作表物件 (sheet)。
    # 2. 使用 Range 方法指定要設定值的儲存格 (value_cell)，
    #    並將其 Value 屬性設置為傳入的 value_to_set。
    # 3. 使用 Range 方法指定要選取的儲存格 (select_cell)，
    #    並調用其 Select 方法來選取該儲存格。
    # 4. 如果操作成功，則打印成功的消息。
    # 5. 如果發生任何異常，則捕獲異常，打印錯誤消息和異常追溯信息。
    try:
        sheet.Range(value_cell).Value = value_to_set  # 設定值 (set value)
        print(f"已將 (has set) 儲存格 (cell) {value_cell} 的值 (value) "
              f"設定 (set) 為 (to) {value_to_set}。")  # 打印
        sheet.Range(select_cell).Select()  # 選取 (select)
        print(f"已選取 (selected) 儲存格 (cell) {select_cell}。")  # 打印
    except Exception as e:  # 捕捉 (catch) 異常 (exception)
        print(
            f"設定 (setting) 儲存格值 (cell value) 或 (or) 選取 "
            f"(selecting) 儲存格 (cell) 時 (when) 發生 (occurred) 錯誤 "
            f"(error): {e}"
        )  # 打印
        traceback.print_exc()  # 打印異常信息 (print exception information)


def run_excel_conditional_formatting(  # 定義函數 (function) 運行 (run) Excel
    # 條件式格式設定 (conditional formatting)
    target_range_address="A1:AA219"  # target_range_address: 要應用條件式
    # 格式設定的目標範圍地址，預設為 "A1:AA219"。
):
    """
    主函數 (main function)，協調 (coordinate) 執行 (execute) 所有 (all)
    條件式格式設定 (conditional formatting) 操作 (operation)。
    """
    # 思路:
    # 1. 調用 initialize_excel 函數來獲取 Excel 應用程式、工作簿和工作表的物件。
    # 2. 如果初始化失敗 (返回 None)，則打印錯誤消息並終止程序。
    # 3. 解包 initialize_excel 返回的 Excel 物件。
    # 4. 調用 clear_conditional_formatting 函數清除工作表中的所有現有條件式格式設定。
    # 5. 使用工作表的 Range 方法根據傳入的 target_range_address 創建目標範圍物件。
    # 6. 調用 apply_border_conditional_formatting 函數將邊框條件式格式設定應用於目標範圍。
    # 7. 調用 apply_font_conditional_formatting 函數將字體顏色條件式格式設定應用於目標範圍。
    # 8. 調用 set_cell_value_and_select 函數設置特定的儲存格值並選取另一個儲存格。
    # 9. 如果所有步驟都成功完成，則打印成功的消息。
    # 10. 如果在執行過程中發生任何異常，則捕獲異常，打印錯誤消息和異常追溯信息。
    # 11. 在 finally 塊中，嘗試解除初始化 COM 組件 (pythoncom.CoUninitialize)。
    excel_objects = initialize_excel()  # 初始化 (initialize) Excel
    if not excel_objects:  # 如果 (if) excel_objects 不是 (not) 真 (true)
        print("初始化 (initialization) 失敗 (failed)，程序 (program) 終止 "
              "(terminated)。")  # 打印
        sys.exit(1)  # 退出 (exit) 程序 (program)

    excel, workbook, sheet = excel_objects  # 解包 (unpack) Excel 對象
    # (objects)
    try:
        clear_conditional_formatting(sheet)  # 清除 (clear) 條件式格式設定
        # (conditional formatting)

        target_range = sheet.Range(target_range_address)  # 目標範圍
        # (target range)
        print(f"目標範圍 (target range) 設定 (set) 為 (to): "
              f"{target_range.Address}")  # 打印

        apply_border_conditional_formatting(target_range)
        # 應用 (apply) 邊框 (border) 條件式格式設定 (conditional formatting)
        apply_font_conditional_formatting(target_range)
        # 應用 (apply) 字體 (font) 條件式格式設定 (conditional formatting)

        set_cell_value_and_select(sheet)  # 設置 (set) 儲存格值 (cell value)
        # 並 (and) 選取 (select)

        print("腳本 (script) 執行 (executed) 成功 (successfully)。")  # 打印
    except Exception as e:  # 捕捉 (catch) 異常 (exception)
        print(
            f"執行 (executing) 主 (main) 操作 (operation) 時 (when) "
            f"發生 (occurred) 錯誤 (error): {e}"
        )  # 打印
        traceback.print_exc()  # 打印異常信息 (print exception information)
    finally:
        try:
            pass
            # excel.Quit()  # 退出 (quit) Excel
            pythoncom.CoUninitialize()  # 解除 (uninitialize) COM
            print("Excel 已關閉 (closed)，COM 已解除 (uninitialized)。")  # 打印
        except Exception as e:  # 捕捉 (catch) 異常 (exception)
            print(
                f"關閉 (closing) Excel 或 (or) 解除 (uninitializing) COM "
                f"時 (when) 發生 (occurred) 錯誤 (error): {e}"
            )  # 打印
            traceback.print_exc()  # 打印異常信息 (print exception information)


if __name__ == "__main__":  # 如果 (if) 是主模塊 (main module)
    run_excel_conditional_formatting()  # 運行 (run) Excel 條件式格式設定
    # (conditional formatting)