def kill_program(program="excel"):  
    # 定义关闭指定程序的函数，默认为excel
    import subprocess  
    # 导入subprocess库，用于执行系统命令
    import os  
    # 导入os库，用于操作系统接口
    import time  
    # 导入time库，用于暂停

    tasklist_command = "tasklist"  
    # 定义获取任务列表的命令
    try:
        tasklist_result = subprocess.run(
            tasklist_command,  
            # 命令
            stdout=subprocess.PIPE,  
            # 标准输出管道
            shell=True,  
            # 使用shell
            text=True,  
            # 以文本模式运行
            encoding='mbcs'  
            # 使用mbcs编码
        )
        tasklist_output = tasklist_result.stdout  
        # 获取命令输出
    except UnicodeDecodeError:  
        # 捕获Unicode解码错误
        tasklist_result = subprocess.run(
            tasklist_command,  
            # 命令
            stdout=subprocess.PIPE,  
            # 标准输出管道
            shell=True,  
            # 使用shell
            text=True,  
            # 以文本模式运行
            encoding='utf-8'  
            # 使用utf-8编码
        )
        tasklist_output = tasklist_result.stdout  
        # 获取命令输出

    with open("data.txt", "w", encoding='utf-8') as f:  
        # 打开data.txt文件，使用utf-8编码写入
        f.write(tasklist_output)  
        # 写入任务列表输出
        f.close()  
        # 关闭文件

    pause_command = ""  
    # 定义暂停命令为空字符串
    os.system(pause_command)  
    # 执行暂停命令

    programs_to_kill = [program]  
    # 定义要关闭的程序列表

    for prog in programs_to_kill:  
        # 遍历要关闭的程序
        findstr_command = f'findstr /i {prog} data.txt > data4.txt'  
        # 定义查找程序的命令
        os.system(findstr_command)  
        # 执行查找命令

        if os.path.getsize("data4.txt") == 0:  
            # 检查data4.txt文件是否为空
            #print(f"{prog} 程序没有运行")  
            # 打印程序没有运行的信息
            continue  
            # 跳过此程序

        taskkill_command = (  
            # 定义关闭程序的命令
            'for /f "tokens=2" %b in (data4.txt) '  
            # 从data4.txt中获取PID
            'do taskkill /f /t /pid %b'  
            # 关闭对应的进程
        )
        os.system(pause_command)  
        # 执行暂停命令

        try:
            taskkill_result = subprocess.run(
                taskkill_command,  
                # 命令
                stdout=subprocess.PIPE,  
                # 标准输出管道
                shell=True,  
                # 使用shell
                text=True,  
                # 以文本模式运行
                encoding='mbcs'  
                # 使用mbcs编码
            )
            taskkill_output = taskkill_result.stdout  
            # 获取命令输出
        except UnicodeDecodeError:  
            # 捕获Unicode解码错误
            taskkill_result = subprocess.run(
                taskkill_command,  
                # 命令
                stdout=subprocess.PIPE,  
                # 标准输出管道
                shell=True,  
                # 使用shell
                text=True,  
                # 以文本模式运行
                encoding='utf-8'  
                # 使用utf-8编码
            )
            taskkill_output = taskkill_result.stdout  
            # 获取命令输出

        print(f"{prog} 已经成功关闭")  
        # 打印程序关闭成功的信息
        time.sleep(0.3)  
        # 暂停0.3秒
    print("over")
#terminate_program()  
# 调用函数关闭excel程序