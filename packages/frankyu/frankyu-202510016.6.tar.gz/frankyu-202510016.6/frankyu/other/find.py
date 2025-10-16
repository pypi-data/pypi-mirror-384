"""
Windows.edb 是 Windows Search 索引文件，主要用于提供内容索引、属性缓存以及文件、电子邮件和其他内容的搜索结果。
由于 Windows 系统默认会对文件进行索引以加快搜索速度，所有与索引有关的数据都存储在这个 edb 文件中。
随着使用时间的增长，Windows.edb 文件可能会变得非常大，占用大量磁盘空间。

操作步骤：
1. 停止 Windows Search 服务以便释放文件锁定。
2. 删除 Windows.edb 文件，释放磁盘空间。
3. 根据需要重新启动 Windows Search 服务并配置其启动类型。
4. 如果希望完全禁用生成 Windows.edb 文件的功能，需要禁用 Windows Search 服务。

注意事项：
- 在操作前，请确保您对系统的操作有足够的权限（以管理员身份运行）。
- 删除 Windows.edb 文件后，若重新启用 Windows Search 服务，该文件会自动重新生成。
"""

# 定义命令字符串，用于控制 Windows Search 服务的启动和停止
aaa = "net stop wsearch"  # 停止 Windows Search 服务的命令
bbb = r"sc config wsearch start= disabled"  # 禁用 Windows Search 服务的自动启动命令
ccc = r"net start wsearch"  # 启动 Windows Search 服务的命令
eee = "sc config wsearch start= delayed-auto"  # 配置 Windows Search 服务的启动类型为延迟自动

# 循环执行停止和禁用服务的命令
for i in [aaa, bbb]:
    import os
    import time
    
    # 使用 os.system 执行系统命令
    # os.system(i)  # 停止服务或禁用自动启动（注释掉以防止误执行）
    
    # 为了安全，延迟 10 秒，确保命令执行完成
    # time.sleep(10)

# 循环执行启动和配置服务的命令
for i in [ccc, eee]:
    import os
    import time
    
    os.system(i)  # 启动服务或配置启动类型
    time.sleep(10)  # 延迟 10 秒，确保命令执行完成