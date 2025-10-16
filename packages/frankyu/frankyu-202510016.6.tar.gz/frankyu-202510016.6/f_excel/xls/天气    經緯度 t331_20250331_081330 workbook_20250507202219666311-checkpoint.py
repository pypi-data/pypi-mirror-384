bbb = r'https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/xls/%E5%A4%A9%E6%B0%94%20%20%20%20%E7%B6%93%E7%B7%AF%E5%BA%A6%20t331_20250331_081330.xlsx'
aaa = '天气    經緯度 t331_20250331_081330 workbook_20250507202219666311'
bbb

import f_excel.over.open_and_process_excel as op

app,book,a = op.open_and_process_excel(bbb)