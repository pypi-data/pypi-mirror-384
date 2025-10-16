aaa = "IPC_2221A_中文版_印制板设计通用标准workbook_xls__20250512161833581607"
print(aaa)

bbb = r"https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/xls/IPC_2221A_%E4%B8%AD%E6%96%87%E7%89%88_%E5%8D%B0%E5%88%B6%E6%9D%BF%E8%AE%BE%E8%AE%A1%E9%80%9A%E7%94%A8%E6%A0%87%E5%87%86workbook_xls__20250512161833581607.xlsx"

import f_excel.d单函数.open_or_add_process_excel_with_r1c1 as op


op.open_or_add_process_excel_with_r1c1(bbb)

from time import *
sleep(10)