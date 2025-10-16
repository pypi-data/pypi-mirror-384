import platform
import os
import subprocess
import sys
import shutil
import psutil


def get_python_version(print_flag=0):
    """
    获取 Python 版本号
    参数:
        print_flag: 是否打印信息，0 表示不打印，1 表示打印
    返回:
        str: Python 版本号字符串，例如 "3.8.5"
    """
    python_version = platform.python_version()  # 获取 Python 版本号
    if print_flag == 1:
        print(f"Python Version: {python_version}")  # 打印 Python 版本号
    return python_version


def get_installed_packages(print_flag=0):
    """
    获取已安装的 Python 库及其版本
    参数:
        print_flag: 是否打印信息，0 表示不打印，1 表示打印
    返回:
        str: 已安装库的列表字符串，格式为 "库名==版本号" 的多行字符串
            例如:
                numpy==1.19.2
                pandas==1.1.3
                ...
            如果发生错误，返回错误信息字符串
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],  # 调用 pip list 命令
            capture_output=True,  # 捕获输出
            text=True  # 输出为文本格式
        )
        installed_packages = result.stdout  # 获取输出结果
        if print_flag == 1:
            print("Installed Packages:")  # 打印标题
            print(installed_packages)  # 打印库列表
        return installed_packages
    except Exception as e:
        error_message = f"Error: {str(e)}"  # 捕获异常
        if print_flag == 1:
            print(error_message)  # 打印错误信息
        return error_message


def get_python_path(print_flag=0):
    """
    获取 Python 解释器的路径
    参数:
        print_flag: 是否打印信息，0 表示不打印，1 表示打印
    返回:
        str: Python 解释器路径字符串，例如 "/usr/bin/python3"
    """
    python_path = sys.executable  # 获取 Python 解释器路径
    if print_flag == 1:
        print(f"Python Path: {python_path}")  # 打印路径
    return python_path


def get_pip_location(print_flag=0):
    """
    获取 pip 的安装路径
    参数:
        print_flag: 是否打印信息，0 表示不打印，1 表示打印
    返回:
        str: pip 安装路径字符串，例如 "/usr/bin/pip"；
             如果 pip 未找到，返回 "pip not found"；
             如果发生错误，返回错误信息字符串
    """
    try:
        pip_path = shutil.which("pip")  # 查找 pip 路径
        if pip_path:
            if print_flag == 1:
                print(f"pip Location: {pip_path}")  # 打印 pip 路径
            return pip_path
        else:
            error_message = "pip not found"  # pip 未找到
            if print_flag == 1:
                print(error_message)  # 打印错误信息
            return error_message
    except Exception as e:
        error_message = f"Error: {str(e)}"  # 捕获异常
        if print_flag == 1:
            print(error_message)  # 打印错误信息
        return error_message


def get_os_info(print_flag=0):
    """
    获取操作系统信息
    参数:
        print_flag: 是否打印信息，0 表示不打印，1 表示打印
    返回:
        dict: 操作系统信息字典，包含以下键值对：
            - os: 操作系统类型，例如 "Windows"、"Linux" 或 "Darwin"
            - os_version: 操作系统版本，例如 "10"（对于 Windows 10）
            - windows_version: Windows 版本详细信息（仅在操作系统为 Windows 时有效），包含以下子键值对：
                - 第一个元素: Windows 产品名称，例如 "Windows 10"
                - 第二个元素: Windows 版本号，例如 "10.0.19041"
    """
    os_info = {
        "os": platform.system(),  # 操作系统类型
        "os_version": platform.release(),  # 操作系统版本
        "windows_version": platform.win32_ver() if platform.system() == "Windows" else None  # Windows 版本信息
    }
    if print_flag == 1:
        print(f"OS: {os_info['os']} {os_info['os_version']}")  # 打印操作系统信息
        if os_info['windows_version']:
            print(f"Windows Version: {os_info['windows_version'][0]} ({os_info['windows_version'][1]})")  # 打印 Windows 版本
    return os_info


def get_username(print_flag=0):
    """
    获取当前登录的用户名
    参数:
        print_flag: 是否打印信息，0 表示不打印，1 表示打印
    返回:
        str: 用户名字符串，例如 "john_doe"
    """
    try:
        username = os.getlogin()  # 获取当前登录用户名
    except Exception:
        username = os.environ.get("USER", "Unknown")  # 在某些系统上可能需要从环境变量获取
    if print_flag == 1:
        print(f"Username: {username}")  # 打印用户名
    return username


def get_cpu_info(print_flag=0):
    """
    获取 CPU 信息
    参数:
        print_flag: 是否打印信息，0 表示不打印，1 表示打印
    返回:
        dict: CPU 信息字典，包含以下键值对：
            - physical_cores: 物理核心数，例如 4
            - total_cores: 总核心数（包括逻辑核心），例如 8
            - cpu_freq: 当前 CPU 频率，单位 MHz，例如 "3599.99 MHz"
            - cpu_usage: CPU 使用率，单位 %，例如 "23.5%"
            - cpu_model: CPU 型号，例如 "Intel64 Family 6 Model 142 Stepping 10, GenuineIntel"
    """
    try:
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),  # 物理核心数
            "total_cores": psutil.cpu_count(logical=True),  # 总核心数（包括逻辑核心）
            "cpu_freq": f"{psutil.cpu_freq().current:.2f} MHz" if hasattr(psutil.cpu_freq(), 'current') else "N/A",  # 当前 CPU 频率
            "cpu_usage": f"{psutil.cpu_percent(interval=1)}%",  # CPU 使用率
            "cpu_model": platform.processor() or "Unknown"  # CPU 型号，某些系统可能返回空字符串
        }
        if print_flag == 1:
            print("\nCPU Information:")  # 打印标题
            print(f"  Model: {cpu_info['cpu_model']}")  # 打印 CPU 型号
            print(f"  Physical Cores: {cpu_info['physical_cores']}")  # 打印物理核心数
            print(f"  Total Cores: {cpu_info['total_cores']}")  # 打印总核心数
            print(f"  CPU Frequency: {cpu_info['cpu_freq']}")  # 打印 CPU 频率
            print(f"  CPU Usage: {cpu_info['cpu_usage']}")  # 打印 CPU 使用率
        return cpu_info
    except PermissionError:
        error_message = "Permission denied: Unable to access CPU information"
        if print_flag == 1:
            print(f"\nCPU Information:")
            print(f"  Error: {error_message}")
        return {"error": error_message}


def get_memory_info(print_flag=0):
    """
    获取内存信息
    参数:
        print_flag: 是否打印信息，0 表示不打印，1 表示打印
    返回:
        dict: 内存信息字典，包含以下键值对：
            - total: 总内存，单位 GB，例如 "15.94 GB"
            - available: 可用内存，单位 GB，例如 "11.23 GB"
            - used: 已用内存，单位 GB，例如 "4.71 GB"
            - percent: 内存使用率，单位 %，例如 "29.6%"
    """
    try:
        memory = psutil.virtual_memory()  # 获取内存信息
        memory_info = {
            "total": f"{memory.total / (1024 ** 3):.2f} GB",  # 总内存
            "available": f"{memory.available / (1024 ** 3):.2f} GB",  # 可用内存
            "used": f"{memory.used / (1024 ** 3):.2f} GB",  # 已用内存
            "percent": f"{memory.percent}%"  # 内存使用率
        }
        if print_flag == 1:
            print("\nMemory Information:")  # 打印标题
            print(f"  Total: {memory_info['total']}")  # 打印总内存
            print(f"  Available: {memory_info['available']}")  # 打印可用内存
            print(f"  Used: {memory_info['used']}")  # 打印已用内存
            print(f"  Usage: {memory_info['percent']}")  # 打印内存使用率
        return memory_info
    except PermissionError:
        error_message = "Permission denied: Unable to access memory information"
        if print_flag == 1:
            print(f"\nMemory Information:")
            print(f"  Error: {error_message}")
        return {"error": error_message}


def get_disk_partitions_info(print_flag=0):
    """
    获取硬盘各分区信息
    参数:
        print_flag: 是否打印信息，0 表示不打印，1 表示打印
    返回:
        dict: 硬盘分区信息字典，键为设备名，值为分区信息字典，包含以下键值对：
            - mount_point: 挂载点，例如 "C:\\"（Windows）或 "/home"（Linux）
            - file_system: 文件系统类型，例如 "NTFS"（Windows）或 "ext4"（Linux）
            - total: 总容量，单位 GB，例如 "232.64 GB"
            - used: 已用容量，单位 GB，例如 "120.32 GB"
            - free: 空闲容量，单位 GB，例如 "112.32 GB"
            - percent: 使用率，单位 %，例如 "51.7%"
            - error: 如果无法访问分区，返回错误信息 "Permission denied"
    """
    try:
        partitions = psutil.disk_partitions()  # 获取所有分区
        disk_info = {}  # 存储分区信息

        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)  # 获取分区使用情况
                disk_info[partition.device] = {
                    "mount_point": partition.mountpoint,  # 挂载点
                    "file_system": partition.fstype,  # 文件系统类型
                    "total": f"{usage.total / (1024 ** 3):.2f} GB",  # 总容量
                    "used": f"{usage.used / (1024 ** 3):.2f} GB",  # 已用容量
                    "free": f"{usage.free / (1024 ** 3):.2f} GB",  # 空闲容量
                    "percent": f"{usage.percent}%"  # 使用率
                }
                if print_flag == 1:
                    print(f"\n  Device: {partition.device}")  # 打印设备名
                    print(f"    Mount Point: {partition.mountpoint}")  # 打印挂载点
                    print(f"    File System: {partition.fstype}")  # 打印文件系统类型
                    print(f"    Total: {disk_info[partition.device]['total']}")  # 打印总容量
                    print(f"    Used: {disk_info[partition.device]['used']}")  # 打印已用容量
                    print(f"    Free: {disk_info[partition.device]['free']}")  # 打印空闲容量
                    print(f"    Usage: {disk_info[partition.device]['percent']}")  # 打印使用率
            except PermissionError:
                disk_info[partition.device] = {
                    "mount_point": partition.mountpoint,  # 挂载点
                    "file_system": partition.fstype,  # 文件系统类型
                    "error": "Permission denied"  # 错误信息
                }
                if print_flag == 1:
                    print(f"\n  Device: {partition.device}")  # 打印设备名
                    print(f"    Mount Point: {partition.mountpoint}")  # 打印挂载点
                    print(f"    File System: {partition.fstype}")  # 打印文件系统类型
                    print(f"    Error: Permission denied")  # 打印错误信息

        return disk_info
    except PermissionError:
        error_message = "Permission denied: Unable to access disk information"
        if print_flag == 1:
            print(f"\nDisk Partitions Information:")
            print(f"  Error: {error_message}")
        return {"error": error_message}


def get_system_info(
    print_python_version=0,
    print_python_path=0,
    print_pip_location=0,
    print_os_info=0,
    print_username=0,
    print_cpu_info=0,
    print_memory_info=0,
    print_disk_info=0,
    print_packages=0
):
    """
    整合所有系统信息，并允许单独控制每个项目的打印
    参数:
        print_python_version: 是否打印 Python 版本，0 表示不打印，1 表示打印
        print_python_path: 是否打印 Python 路径，0 表示不打印，1 表示打印
        print_pip_location: 是否打印 pip 路径，0 表示不打印，1 表示打印
        print_os_info: 是否打印操作系统信息，0 表示不打印，1 表示打印
        print_username: 是否打印用户名，0 表示不打印，1 表示打印
        print_cpu_info: 是否打印 CPU 信息，0 表示不打印，1 表示打印
        print_memory_info: 是否打印内存信息，0 表示不打印，1 表示打印
        print_disk_info: 是否打印硬盘分区信息，0 表示不打印，1 表示打印
        print_packages: 是否打印已安装库列表，0 表示不打印，1 表示打印
    返回:
        dict: 系统信息字典，包含以下键值对：
            - python_version: Python 版本号字符串
            - python_path: Python 解释器路径字符串
            - pip_location: pip 安装路径字符串，或错误信息
            - os_info: 操作系统信息字典
            - username: 用户名字符串
            - cpu_info: CPU 信息字典
            - memory_info: 内存信息字典
            - disk_partitions_info: 硬盘分区信息字典
            - installed_packages: 已安装库列表字符串，或错误信息
    """
    system_info = {
        "python_version": get_python_version(print_python_version),  # 获取并打印 Python 版本
        "python_path": get_python_path(print_python_path),  # 获取并打印 Python 路径
        "pip_location": get_pip_location(print_pip_location),  # 获取并打印 pip 路径
        "os_info": get_os_info(print_os_info),  # 获取并打印操作系统信息
        "username": get_username(print_username),  # 获取并打印用户名
        "cpu_info": get_cpu_info(print_cpu_info),  # 获取并打印 CPU 信息
        "memory_info": get_memory_info(print_memory_info),  # 获取并打印内存信息
        "disk_partitions_info": get_disk_partitions_info(print_disk_info),  # 获取并打印硬盘分区信息
        "installed_packages": get_installed_packages(print_packages)  # 获取并打印已安装库列表
    }
    return system_info


# 执行并获取信息
if __name__ == "__main__":
    # 示例：打印所有信息
    system_info = get_system_info(
        print_python_version=1,
        print_python_path=1,
        print_pip_location=1,
        print_os_info=1,
        print_username=1,
        print_cpu_info=1,
        print_memory_info=1,
        print_disk_info=0,
        print_packages=0
    )
    
    # 示例：仅打印 Python 版本和 CPU 信息
    # system_info = get_system_info(
    #     print_python_version=1,
    #     print_cpu_info=1
    # )