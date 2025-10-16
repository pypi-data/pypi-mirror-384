bbb = r'https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/xls/%E6%A8%A1%E6%9D%BF-%E9%9D%9E%E5%B8%B8%E9%87%8D%E8%A6%81/%E5%89%AF%E6%9C%AC%E5%AE%B6%E5%BA%AD%E8%B4%A6%E7%B0%BF%E6%9B%B4%E6%96%B0%E4%BA%8E2025%E5%B9%B42%E6%9C%887%E6%97%A5.xlsx'
aaa = '副本家庭账簿更新于2025年2月7日_20250507201736308190'
bbb

import f_excel.over.open_and_process_excel as op

app,book,a = op.open_and_process_excel(bbb)