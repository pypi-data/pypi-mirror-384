import platform  # 用于获取当前操作系统的类型（如 Windows, Linux, Darwin）
import os  # 提供与操作系统交互的功能（例如执行命令）
import sys  # 提供系统特定的参数和函数（如退出程序）
import wmi  # 用于在 Windows 上使用 WMI 查询网络适配器信息
import subprocess  # 用于运行外部命令并捕获其输出（如 ip link）

# 尝试导入 wmi 库，并检查是否安装成功（仅限 Windows 平台）
try:
    import wmi
except ImportError:
    if platform.system() == 'Windows':
        print("请安装 pywin32 库以支持 Windows 平台: pip install pywin32")
        sys.exit(1)  # 如果是 Windows 且未安装 wmi，则退出程序

def list_network_adapters(IPEnabled=True):
    """
    根据当前操作系统调用不同的函数来列出所有网络适配器的信息。
    
    参数：
        无
    
    返回值：
        List[Dict] - 包含每个网络适配器信息的字典列表，格式如下：
            {
                '名称': str,
                'IP': str,
                'MAC': str,
                '状态': str
            }
    """

    system_type = platform.system()  # 获取当前操作系统类型，如 'Windows', 'Linux', 'Darwin'

    if system_type == 'Windows':
        return list_network_adapters_windows(IPEnabled=IPEnabled)  # Windows 使用 WMI 查询适配器信息
    elif system_type in ['Linux', 'Darwin']:  # Darwin 是 macOS 的内核名
        return list_network_adapters_unix()  # Linux/macOS 使用 shell 命令查询
    else:
        print("不支持的操作系统")  # 不支持的系统类型
        return []  # 返回空列表表示没有找到适配器



def list_network_adapters_windows(IPEnabled=True):
    """
    在 Windows 系统上列出所有已启用 IP 的网络适配器信息。

    参数：
        无

    返回值：
        List[Dict] - 包含每个网络适配器信息的字典列表
    """

    c = wmi.WMI()  # 创建一个 WMI 对象用于访问 Windows 管理数据
    adapters = []  # 存储适配器信息的列表

    # 遍历所有已启用 IPv4 的网络适配器配置
    for adapter in c.Win32_NetworkAdapterConfiguration(IPEnabled=IPEnabled):   #(IPEnabled=True):   (IPEnabled=0):
        ip_address = ', '.join(adapter.IPAddress) if adapter.IPAddress else '无'  # 获取 IP 地址，如果没有则为“无”
        mac_address = adapter.MACAddress if adapter.MACAddress else '无'  # 获取 MAC 地址，如果没有则为“无”
        status = '已启用' if adapter.IPEnabled else '未启用'  # 根据 IPEnabled 属性判断状态
        description = adapter.Description  # 获取适配器描述作为名称

        # 构建适配器信息字典并加入列表
        adapters.append({
            '名称': description,  # 适配器描述
            'IP': ip_address,  # IP 地址
            'MAC': mac_address,  # MAC 地址
            '状态': status  # 当前状态
        })

    return adapters  # 返回包含所有适配器信息的列表

def list_network_adapters_unix():
    """
    在 Linux 或 macOS 系统上列出所有网络适配器信息。

    参数：
        无

    返回值：
        List[Dict] - 包含每个网络适配器信息的字典列表
    """

    # 运行 `ip -o -br addr show` 命令，获取简化的网络接口信息
    result = subprocess.run(['ip', '-o', '-br', 'addr', 'show'], stdout=subprocess.PIPE)
    lines = result.stdout.decode().splitlines()  # 解析命令输出成多行字符串列表
    adapters = []  # 存储适配器信息的列表

    # 遍历每一行输出
    for line in lines:
        parts = line.split()  # 分割每行内容
        name = parts[0]  # 第一列是适配器名称

        # 提取 IP 地址部分（忽略 inet 和 inet6 标签）
        ips = [part.split('/')[0] for part in parts[2:] if part not in ['inet', 'inet6']]
        ip_address = ', '.join(ips) if ips else '无'  # 如果有多个 IP，就连接起来；否则显示“无”

        # 获取 MAC 地址（从 /sys/class/net/<name>/address 文件中读取）
        mac_result = subprocess.run(['cat', f'/sys/class/net/{name}/address'], stdout=subprocess.PIPE)
        mac_address = mac_result.stdout.decode().strip() if mac_result.returncode == 0 else '无'

        # 获取网卡状态（up/down），通过读取 operstate 文件
        status_result = subprocess.run(['cat', f'/sys/class/net/{name}/operstate'], stdout=subprocess.PIPE)
        status = status_result.stdout.decode().strip() if status_result.returncode == 0 else '未知'

        # 构建适配器信息字典并加入列表
        adapters.append({
            '名称': name,  # 适配器名称
            'IP': ip_address,  # IP 地址
            'MAC': mac_address,  # MAC 地址
            '状态': status  # 状态（up/down/unknown）
        })

    return adapters  # 返回包含所有适配器信息的列表