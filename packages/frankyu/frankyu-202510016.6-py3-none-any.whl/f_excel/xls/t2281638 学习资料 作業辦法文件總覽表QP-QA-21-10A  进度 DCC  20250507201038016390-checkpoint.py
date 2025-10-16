bbb = r'https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/xls/t2281638%20%E5%AD%A6%E4%B9%A0%E8%B5%84%E6%96%99%20%E4%BD%9C%E6%A5%AD%E8%BE%A6%E6%B3%95%E6%96%87%E4%BB%B6%E7%B8%BD%E8%A6%BD%E8%A1%A8QP-QA-21-10A%20%20%E8%BF%9B%E5%BA%A6%20DCC.xlsx'
aaa = 't2281638 学习资料 作業辦法文件總覽表QP-QA-21-10A  进度 DCC  20250507201038016390'
bbb

import f_excel.over.open_and_process_excel as op

app,book,a = op.open_and_process_excel(bbb)