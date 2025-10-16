import subprocess
import platform
import time
import datetime
import logging
import importlib.util
import tkinter as tk
from tkinter import messagebox

# 配置日志
logging.basicConfig(
    filename='ping_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_and_install(package_name):
    """检查模块是否存在，不存在则尝试安装"""
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        logging.warning(f"{package_name} 未找到，正在尝试安装...")
        try:
            subprocess.check_call(["pip", "install", package_name])
            logging.info(f"{package_name} 安装成功")
        except Exception as e:
            logging.error(f"安装 {package_name} 失败: {e}")
            raise ImportError(f"无法安装 {package_name}")

check_and_install('f_other.over.set_volume_1')

from f_other.over.set_volume_1 import set_volume

def is_pingable(target):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', target]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        success = result.returncode == 0
        log_level = logging.INFO if success else logging.ERROR
        logging.log(log_level, f"Ping {target} {'成功' if success else '失败'}")
        return success
    except Exception as e:
        logging.error(f"发生错误: {e}")
        return False

def start_check(url_entry):
    url = url_entry.get()
    if not url:
        messagebox.showerror("输入错误", "请输入有效的URL或IP地址")
        return
    
    def run_check():
        clean_url = url.split(':')[0]
        set_volume(0.1)
        
        if is_pingable(clean_url):
            set_volume(0.9)
        else:
            while not is_pingable(clean_url):
                print(f"[{datetime.datetime.now()}] {clean_url} 不可达，继续等待...")
                time.sleep(3)
            set_volume(0.7)
    
    # 在新线程中运行，避免阻塞GUI主线程
    import threading
    threading.Thread(target=run_check).start()

# 创建GUI
root = tk.Tk()
root.title("Ping检测与音量调整")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="请输入要检测的URL或IP地址:")
label.pack(side=tk.LEFT)

entry = tk.Entry(frame, width=50)
entry.pack(side=tk.LEFT)

button = tk.Button(root, text="开始检测", command=lambda: start_check(entry))
button.pack(pady=10)

root.mainloop()