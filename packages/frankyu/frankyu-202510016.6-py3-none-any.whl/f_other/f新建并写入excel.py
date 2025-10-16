#!/usr/bin/env python
# coding: utf-8

# 导入用于 Excel 操作的 Python 库 xlwings
import xlwings

# 导入用户自定义模块 frankyu
import frankyu

# 导入 frankyu 模块中的 excel 子模块
import frankyu.excel

# 为了简化后续代码，将 frankyu.excel 模块赋值给变量 ex
ex = frankyu.excel

# 初始化 Excel 应用程序，通过自定义模块中的方法进行初始化
app = ex.initialize_excel()

# 创建一个新的 Excel 工作簿，通过自定义模块中的方法进行创建
book = ex.create_workbook(app)

def excelpid():
    """
    获取当前运行的第一个 Excel 应用程序的进程 ID (PID)。

    思路:
    1. 遍历 xlwings 提供的所有运行中的 Excel 应用程序实例。
    2. 获取每个实例的进程 ID (PID) 并存储到列表中。
    3. 返回第一个应用程序实例的 PID。

    方法清单:
    - xlwings.apps: 获取所有运行中的 Excel 应用程序实例。
    - app.pid: 获取 Excel 应用程序实例的进程 ID (PID)。

    返回值:
        int: 当前运行的第一个 Excel 应用程序的 PID。
    """
    bbb = []  # 初始化存储所有 Excel 应用程序 PID 的列表

    for i in xlwings.apps:
        # 遍历所有运行中的 Excel 应用程序实例

        aaa = i.pid
        # 获取当前 Excel 应用程序的 PID

        bbb.append(aaa)
        # 将当前 Excel 应用程序的 PID 添加到列表中

    app = xlwings.apps[bbb[0]]
    # 获取列表中第一个 Excel 应用程序实例，通过其 PID

    return app.pid
    # 返回第一个 Excel 应用程序实例的 PID

# 调用 excelpid 函数
excelpid()


# 获取当前 Excel 应用程序的 PID
eee = excelpid()

# 获取第一个工作薄的第一个工作表中的单元格 A1
rng = xlwings.apps[eee].books[0].sheets[0].range("A1")

# 将公式 "=2+3" 设置为单元格 A1 的值
rng.value = "=2+3"

# 打印所有运行中的 Excel 应用程序实例
xlwings.apps

# 遍历并打印所有运行中的 Excel 实例及其打开的工作簿名称
for i in xlwings.apps:
    # 遍历所有运行中的 Excel 应用程序实例
    print(i.pid)
    # 打印当前 Excel 应用程序的 PID

    for j in i.books:
        # 遍历当前 Excel 应用程序打开的所有工作簿
        print()
        print(j.name)
        # 打印当前工作簿的名称

# 打印当前活动单元格所在的 Excel 应用程序的 PID
rng.sheet.book.app.pid

# 导入 Python 的 time 模块，用于时间延迟
import time

# 设置延迟 4 秒，确保 Excel 实例稳定
time.sleep(4)

# 关闭由 excelpid 函数返回的 Excel 应用程序实例
xlwings.apps[excelpid()].quit()