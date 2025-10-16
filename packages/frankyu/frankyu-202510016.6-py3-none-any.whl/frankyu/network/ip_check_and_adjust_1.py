import subprocess
import platform
import re
import time
import datetime

def check_and_adjust(url, low_volume=0.1, high_volume=0.7, medium_volume=0.6, ping_interval=3):
    """
    持续检查指定的URL是否可以ping通，根据结果调整音量。

    参数:
        url (str): 要ping的网址或IP地址（可包含端口号，如 "127.1.1.1:7777"）。
        low_volume (float): 初始和不可达时设置的低音量（默认 0.1）。
        high_volume (float): 首次可达时设置的高音量（默认 0.9）。
        medium_volume (float): 后续恢复可达时设置的中等音量（默认 0.7）。
        ping_interval (int): 不可达时检查间隔时间（秒，默认 3 秒）。
    """
    from f_other.over.set_volume_1 import set_volume

    # 去除 URL 中可能带的端口号，只保留主机部分
    clean_url = url.split(':')[0]

    # 初始设置为低音量
    set_volume(low_volume)

    def is_pingable(target):
        """内部函数：判断目标是否可以ping通"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', target]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"发生错误: {e}")
            return False

    # 如果当前是通的，设置高音量
    if is_pingable(clean_url):
        set_volume(high_volume)
        print("OK")
    else:
        # 否则持续尝试直到通为止，每隔一段时间 ping 一次
        while not is_pingable(clean_url):
            print(f"[{datetime.datetime.now()}] {clean_url} 不可达，继续等待...")
            time.sleep(ping_interval)

        # 可达后设置中等音量
        set_volume(medium_volume)


# 示例调用
if __name__ == "__main__":
    bbb = "intel-mini:7777"
    check_and_adjust(bbb)