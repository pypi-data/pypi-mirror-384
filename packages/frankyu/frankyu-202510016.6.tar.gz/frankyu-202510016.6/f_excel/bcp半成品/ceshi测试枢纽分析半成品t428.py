#!/usr/bin/env python
# coding: utf-8

# In[1]:


import f_other.deepseek_python_20250427_416a78 as de

app = de.initialize_excel()


# In[2]:


app


# In[3]:


book = de.open_workbook(excel_app=app)


# In[4]:


sh = book.Worksheets(1).Name
sh


# In[5]:


sheet = de.copy_worksheet(workbook=book,sheet_name=book.Worksheets(1).Name)


# In[6]:


sheet.Name


# In[7]:


table = de.create_list_object(worksheet=sheet)


# In[8]:


table


# In[9]:


#table.DisplayName = "t2_"


# In[10]:


table.DisplayName


# In[11]:


table.Comment


# In[12]:


table.Active


# In[13]:


table.AlternativeText


# In[14]:


table.Application


# In[15]:


table.AutoFilter


# In[16]:


table.CLSID


# In[17]:


table.coclass_clsid


# In[18]:


table.Comment


# In[19]:


table.Creator


# In[20]:


table.DataBodyRange


# In[21]:


table.XmlMap


# In[22]:


table.TotalsRowRange


# In[23]:


table.TableStyle


# In[24]:


table.Summary


# In[25]:


table.SourceType


# In[26]:


table.Sort


# In[27]:


table.ShowTotals


# In[28]:


table.Slicers


# In[29]:


table


# In[30]:


#de.add_formula_columns()


# In[31]:


sheet.Range("K1").Value = "len"


# In[32]:


sheet.Range("L1").Value = "cou"


# In[33]:


#import frankyu.frankyu as fr


# In[34]:


#import frankyu.kill_program as gbc


# In[35]:


#gbc.kill_program("excel")


# In[36]:


#app.Quit()
aaa= r'''
#de.add_formula_columnsdef add_formula_columns(worksheet: win32.CDispatch, len_col: str = "K", count_col: str = "L", ref_col: str = "SN_NO") -> None:

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
File:      c:\anaconda3\lib\site-packages\f_other\deepseek_python_20250427_416a78.py
Type:      function
# In[37]:
'''

sheet.Range("K2").Value = "=len([@[SN_NO]])"


# In[38]:


sheet.Range("L2").Value = "=countifs(E:E,[@[SN_NO]])"


# In[39]:

aaa= r'''
#de.main



        # 第6步: 創建數據透視表。
        print("正在創建數據透視表...")
        # 調用 create_pivot_table 函數，傳遞工作簿對象、結構化表格的 Range 對象作為數據源，並指定新透視表工作表名稱為 "分析報表"。
        pivot_table, pivot_sheet = create_pivot_table(
            workbook,
            source_range=source_range, # 使用結構化表格的 Range 對象作為數據源
            pivot_sheet_name="分析報表" # 指定新透視表工作表的名稱
        )
        print(f"數據透視表創建成功，位於工作表: {pivot_sheet.Name}")

# In[40]:

'''
tsb_yuayuanzhu  = de.create_pivot_table(workbook=book,source_range=table.Range,pivot_sheet_name="422233",start_cell="A1",pivot_name="4546456")


# In[41]:


sheet2 = tsb_yuayuanzhu[1]
sheet2.Name


# In[42]:


toushubiao = tsb_yuayuanzhu[0]
toushubiao


# In[ ]:





# In[ ]:





# In[ ]:

aaa= r'''



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
File:      c:\anaconda3\lib\site-packages\f_other\deepseek_python_20250427_416a78.py
Type:      function
# In[43]:

'''
#app.Quit()


# In[ ]:


import frankyu.frankyu as fr
fr.countdown(30)





