import win32com.client
# 导入 win32com.client 模块，用于与 Microsoft Office 应用程序进行交互

import datetime
# 导入 datetime 模块，用于处理日期和时间

import os
# 导入 os 模块，用于文件和系统操作

import time
# 导入 time 模块，用于延时操作

import psutil
# 导入 psutil 模块，用于获取系统电池信息

import subprocess
# 导入 subprocess 模块，用于执行系统命令

import win32clipboard
# 导入 win32clipboard 模块，用于操作剪贴板

import win32gui
import win32ui
import win32con
import win32api
# 导入 win32 系列模块，用于操作窗口和截图功能

# 用于安装 Python 包的通用函数
def install_package_with_pip(pip_executable_path="pip.exe", package_name="pandas",mirror_source = r"https://pypi.tuna.tsinghua.edu.cn/simple/" ):

    """
    使用指定的 pip 可执行文件路径和包名来安装 Python 包。
    
    :param pip_executable_path: pip 可执行文件的路径，默认为 D 盘 Python3.13 版本的 pip 路径
    
    :param package_name: 要安装的包名，默认为 pandas
        pip_command = f"{pip_executable_path} install -i {mirror_source} {package_name}"
        print("Executing command:", pip_command)
        os.system(pip_command)  # 执行 pip 命令
        print("Installation Complete.")    
    """
    import os
    if mirror_source:
        
    
        pip_command = f"{pip_executable_path} install -i {mirror_source} {package_name}"
        print("Executing command:", pip_command)
        os.system(pip_command)  # 执行 pip 命令
        print("Installation Complete.")
    else:
        pip_command = f"{pip_executable_path}  install  {package_name}"
        print("Executing command:", pip_command)
        os.system(pip_command)  # 执行 pip 命令
        print("Installation Complete.")        
# 使用默认的 Python 3.10 pip 安装指定包
def install_package_with_python310_default_pip(package_name="xlwings"):
    """
    使用默认的 Python 3.10 pip 可执行文件路径来安装指定的包。
    
    :param package_name: 要安装的包名，默认为 xlwings
    """
    install_package_with_pip(pip_executable_path=r"C:\Users\Public\Python310\Scripts\pip.exe", package_name=package_name)

# 打开指定盘符
def startT(pan="T:"):
    """
    打开指定盘符路径。
    
    :param pan: 盘符路径，默认为 T:
    """
    os.system(f"start {pan}")
    print(f"{pan} 已经成功打开")
    time.sleep(2)

# 十进制转换为其他进制
def shijinzhi2other(shi, jishu):
    """
    将十进制数字转换为其他进制表示。
    
    :param shi: 十进制数字
    :param jishu: 目标进制
    :return: 转换后的字符串表示
    """
    shijinzhi = [i for i in range(0, 10 + 26)]
    shiliu = [str(i) for i in range(0, 10)] + [i for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    dic = dict(zip(shijinzhi, shiliu))  # 字典对照表
    lis = []
    while shi:
        shang, yu = divmod(shi, jishu)
        lis.append(dic[yu])
        shi = shang
    return ''.join(reversed(lis))

# 获取电池状态
def dianliang():
    """
    获取电池状态信息，并打印电池电量百分比。
    """
    import psutil
    battery = psutil.sensors_battery()
    if battery is None:
        print("No battery is found.")
        #exit()
    else:
        
    
        percentage = battery.percent
        print(f"Battery Percentage: {percentage}%")
# 截图并通过邮件发送
def jietu2mail():
    """
    截图桌面并通过 Outlook 邮件发送。
    """
    jietu_file = r"C:\Users\Public\jietu.bmp"
    hdesktop = win32gui.GetDesktopWindow()
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (0, 0), win32con.SRCCOPY)
    screenshot.SaveBitmapFile(mem_dc, jietu_file)
    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())
    
    app = win32com.client.Dispatch("outlook.application")
    mail = app.CreateItem(0)
    mail.To = "yufengguang@hotmail.com"
    mail.CC = "frank_yu@prime3c.com"
    mail.Subject = f"截图 {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    mail.Attachments.Add(jietu_file)
    mail.Body = "请查收截图。"
    mail.Send()

# 倒计时函数
def countdown(t):
    """
    divmod
        while t:
        years, remainder = divmod(t, 31536000)
        days, remainder = divmod(remainder, 86400)
        hours, remainder = divmod(remainder, 3600)
        mins, secs = divmod(remainder, 60)
        timer = f'{years:02}:{days:02}:{hours:02}:{mins:02}:{secs:02}'
        print(timer, end="\r")
        time.sleep(1)
        t -= 1
    print('倒计时结束!')
    
    倒计时函数，接受一个整数 t 作为倒计时的秒数。
    格式化输出为 YY:DD:HH:MM:SS，其中 YY 为年数。
    """
    print("YY:DD:HH:MM:SS")
    while t:
        years, remainder = divmod(t, 31536000)
        days, remainder = divmod(remainder, 86400)
        hours, remainder = divmod(remainder, 3600)
        mins, secs = divmod(remainder, 60)
        timer = f'{years:02}:{days:02}:{hours:02}:{mins:02}:{secs:02}'
        print(timer, end="\r")
        time.sleep(1)
        t -= 1
    print("00:00:00:00:00")
    print(f'{t}秒倒计时结束!')

# 主函数
if __name__ == '__main__':
    print("实用工具函数已加载。")
    daoJiShi_t2 = lambda t=3600: countdown(t)
    daoJiShi_t2(10)  # 测试倒计时 10 秒