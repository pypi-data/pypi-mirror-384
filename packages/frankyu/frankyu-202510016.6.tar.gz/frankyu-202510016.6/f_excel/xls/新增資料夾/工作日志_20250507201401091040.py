bbb = r'https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/xls/sc27-xls/%E5%B7%A5%E4%BD%9C%E6%97%A5%E5%BF%97.xlsx'
aaa = '工作日志_20250507201401091040'
bbb

import f_excel.over.open_and_process_excel as op

app,book,a = op.open_and_process_excel(bbb)