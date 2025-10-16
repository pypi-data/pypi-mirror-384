#!/usr/bin/env python
# coding: utf-8

# 定义函数 `xinJianBook`，用于新建一个 Excel 工作簿
def xinJianBook():
    import frankyu.excel as ex
    # 导入自定义模块 `frankyu.excel`

    app = ex.initialize_excel()
    # 初始化 Excel 应用程序

    ex.create_workbook(app)
    # 创建一个新的工作簿

    # 再次导入 `frankyu.excel` 并重复创建工作簿（可能为冗余代码）
    import frankyu.excel as ex
    app = ex.initialize_excel()
    ex.create_workbook(app)


# 定义函数 `excelpid`，用于获取当前 Excel 应用程序的进程 ID
def excelpid():
    import xlwings
    # 导入 `xlwings` 模块，用于操作 Excel 应用程序

    bbb = []
    # 初始化列表，用于存储所有运行中的 Excel 应用程序的进程 ID

    for i in xlwings.apps:
        # 遍历所有运行中的 Excel 应用程序实例
        bbb.append(i.pid)
        # 将当前应用程序的进程 ID 添加到列表中

    if len(bbb) >= 1:
        # 如果存在运行中的 Excel 应用程序实例
        return bbb[0]
        # 返回第一个应用程序的进程 ID
    else:
        # 如果没有运行中的 Excel 应用程序实例
        xinJianBook()
        # 调用 `xinJianBook` 函数，创建一个新的 Excel 应用程序和工作簿

        import xlwings
        # 再次导入 `xlwings` 模块，确保可以访问新的 Excel 应用程序实例

        bbb = []
        # 初始化新的列表，用于存储新创建的 Excel 应用程序实例的进程 ID

        for i in xlwings.apps:
            # 遍历所有运行中的 Excel 应用程序实例
            bbb.append(i.pid)
            print(i.pid)
            # 打印每个应用程序的进程 ID（用于调试）

        return bbb[0]
        # 返回新创建的第一个应用程序的进程 ID


# 定义函数 `xieRuBiaoGe`，用于在 Excel 表格中写入数据
def xieRuBiaoGe(timeWait=4):
    # 参数 `timeWait` 用于指定保存 Excel 文件前的延迟时间（默认为 4 秒）

    excelpid()
    # 调用 `excelpid` 函数，确保至少有一个运行中的 Excel 应用程序实例

    import xlwings
    # 导入 `xlwings` 模块

    rng = xlwings.apps[excelpid()].books[0].sheets[0].range("A1")
    # 获取运行中的第一个 Excel 应用程序的第一个工作簿的第一个工作表中的单元格范围 A1

    rng.value = "=2+454645657567657567"
    # 将公式 `=2+454645657567657567` 写入单元格 A1

    sheet = rng.sheet
    # 获取当前单元格所在的工作表

    book = sheet.book
    # 获取当前工作表所在的工作簿

    app = book.app
    # 获取当前工作簿所在的 Excel 应用程序

    import frankyu.excel as exc
    import datetime
    # 导入 `frankyu.excel` 模块和 `datetime` 模块

    path = str(datetime.datetime.now()).replace(":", " ").replace("-", " ").replace(".", " ").replace(":", " ").replace(" ", "")
    # 获取当前时间并将其转换为字符串，同时替换特殊字符为空格

    import os
    # 导入 `os` 模块，用于文件路径操作

    path2 = "".join([os.getcwd(), "\\", path, ".xlsx"])
    # 构建保存文件的路径，文件名为当前时间字符串，扩展名为 `.xlsx`

    book.save(path2)
    # 将工作簿保存到指定路径

    import time
    # 导入 `time` 模块，用于延迟操作

    time.sleep(timeWait)
    # 延迟指定的秒数

    app.quit()
    # 关闭 Excel 应用程序