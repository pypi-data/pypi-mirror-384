bbb = 'Realtek RTL8852BE WiFi 6 802.11ax PCIe Adapter'
import platform  # 导入 platform 模块：用于获取当前操作系统的类型（如 Windows, Linux, Darwin）
import os         # 导入 os 模块：提供与操作系统交互的功能，比如执行命令
import sys        # 导入 sys 模块：提供系统特定的参数和函数，例如退出程序
import wmi        # 导入 wmi 模块：用于在 Windows 上使用 WMI 查询网络适配器信息
import subprocess # 导入 subprocess 模块：用于运行外部命令并捕获其输出，例如 ip link

# 尝试导入 wmi 模块，并检查是否安装成功（仅限 Windows 平台）
try:
    import wmi
except ImportError:
    if platform.system() == 'Windows':
        print("请安装 pywin32 库以支持 Windows 平台: pip install pywin32")
        sys.exit(1)  # 如果是 Windows 且未安装 wmi，则退出程序

def list_network_adapters():
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

    system_type = platform.system()  # 调用 platform.system() 方法获取当前操作系统类型（Windows / Linux / Darwin）
    # system_type 是一个字符串，例如 'Windows'、'Linux'、'Darwin'

    if system_type == 'Windows':
        return list_network_adapters_windows()  # 如果是 Windows，调用 list_network_adapters_windows 函数
    elif system_type in ['Linux', 'Darwin']:  # Darwin 是 macOS 的内核名
        return list_network_adapters_unix()  # 如果是 Linux 或 macOS，调用 list_network_adapters_unix 函数
    else:
        print("不支持的操作系统")  # 如果是其他系统，打印错误信息
        return []  # 返回空列表表示没有找到适配器

def list_network_adapters_windows():
    """
    在 Windows 系统上列出所有已启用 IP 的网络适配器信息。

    参数：
        无

    返回值：
        List[Dict] - 包含每个网络适配器信息的字典列表
    """

    c = wmi.WMI()  # 创建一个 WMI 对象 c，用于访问 Windows 管理数据（WMI 是 Windows 的管理接口）
    adapters = []  # 定义一个空列表 adapters，用于存储适配器信息

    # 遍历所有已启用 IPv4 的网络适配器配置
    for adapter in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
        # Win32_NetworkAdapterConfiguration 是 WMI 提供的类，用于查询网络适配器的配置
        # IPEnabled=True 表示只查询已启用 IPv4 的适配器

        # 获取 IP 地址，如果没有则为“无”
        ip_address = ', '.join(adapter.IPAddress) if adapter.IPAddress else '无'
        # IPAddress 是 WMI 提供的属性，返回该适配器的 IP 地址列表

        # 获取 MAC 地址，如果没有则为“无”
        mac_address = adapter.MACAddress if adapter.MACAddress else '无'
        # MACAddress 是 WMI 提供的属性，返回该适配器的 MAC 地址

        # 根据 IPEnabled 属性判断状态
        status = '已启用' if adapter.IPEnabled else '未启用'
        # IPEnabled 是 WMI 提供的布尔属性，表示该适配器是否启用 IPv4

        # 获取适配器描述作为名称
        description = adapter.Description
        # Description 是 WMI 提供的属性，返回该适配器的描述（如 "Realtek PCIe GbE Family Controller"）

        # 构建适配器信息字典并加入列表
        adapters.append({
            '名称': description,  # 适配器描述
            'IP': ip_address,     # IP 地址
            'MAC': mac_address,   # MAC 地址
            '状态': status        # 当前状态
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
    result = subprocess.run(
        ['ip', '-o', '-br', 'addr', 'show'],  # 命令参数：-o 显示所有接口，-br 简化输出
        stdout=subprocess.PIPE  # 将标准输出重定向到 PIPE，以便后续读取
    )
    lines = result.stdout.decode().splitlines()  # 将命令输出解码为字符串并按行分割
    adapters = []  # 定义一个空列表 adapters，用于存储适配器信息

    # 遍历每一行输出
    for line in lines:
        parts = line.split()  # 将每行内容按空格分割成多个部分
        name = parts[0]  # 第一列是适配器名称（如 eth0、wlan0）

        # 提取 IP 地址部分（忽略 inet 和 inet6 标签）
        ips = [part.split('/')[0] for part in parts[2:] if part not in ['inet', 'inet6']]
        # parts[2:] 是 IP 地址部分（如 192.168.1.1/24），split('/')[0] 提取不带子网掩码的部分
        ip_address = ', '.join(ips) if ips else '无'  # 如果有多个 IP，就连接起来；否则显示“无”

        # 获取 MAC 地址（从 /sys/class/net/<name>/address 文件中读取）
        mac_result = subprocess.run(
            ['cat', f'/sys/class/net/{name}/address'],  # cat 命令读取文件内容
            stdout=subprocess.PIPE
        )
        mac_address = mac_result.stdout.decode().strip() if mac_result.returncode == 0 else '无'
        # returncode == 0 表示命令执行成功，否则返回“无”

        # 获取网卡状态（up/down），通过读取 operstate 文件
        status_result = subprocess.run(
            ['cat', f'/sys/class/net/{name}/operstate'],
            stdout=subprocess.PIPE
        )
        status = status_result.stdout.decode().strip() if status_result.returncode == 0 else '未知'

        # 构建适配器信息字典并加入列表
        adapters.append({
            '名称': name,       # 适配器名称（如 eth0）
            'IP': ip_address,   # IP 地址
            'MAC': mac_address, # MAC 地址
            '状态': status      # 状态（up/down/unknown）
        })

    return adapters  # 返回包含所有适配器信息的列表

def toggle_network_adapter(adapter_name):
    """
    根据当前状态切换指定网络适配器的状态（如果启用则禁用，反之亦然）。

    参数：
        adapter_name (str): 要切换状态的网络适配器名称

    返回值：
        Tuple[bool, str]: 
            - 成功与否的布尔值
            - 附加信息（成功或失败原因）
    """

    system_type = platform.system()  # 获取当前操作系统类型

    if system_type == 'Windows':
        return toggle_network_adapter_windows(adapter_name)  # 调用 Windows 版本
    elif system_type in ['Linux', 'Darwin']:
        return toggle_network_adapter_unix(adapter_name)  # 调用 Unix/Linux/macOS 版本
    else:
        print("不支持的操作系统")  # 不支持的系统
        return False, "不支持的操作系统"

def toggle_network_adapter_windows(adapter_name):
    """
    Windows 上切换指定网络适配器的状态。

    参数：
        adapter_name (str): 网络适配器的描述名称（如 "Realtek PCIe GbE Family Controller"）

    返回值：
        Tuple[bool, str]: 
            - 成功与否的布尔值
            - 附加信息（成功或失败原因）
    """

    try:
        c = wmi.WMI()  # 创建 WMI 对象
        adapters = c.Win32_NetworkAdapter(Description=adapter_name)  # 查找匹配的适配器
        # Win32_NetworkAdapter 是 WMI 提供的类，用于查询网络适配器的基本信息
        # Description=adapter_name 表示按描述名称查找适配器

        if not adapters:
            print(f"找不到描述为 '{adapter_name}' 的网络适配器")  # 未找到适配器
            return False, f"未找到名称为 {adapter_name} 的网卡"

        for adapter in adapters:
            current_status = adapter.NetConnectionStatus  # 获取当前状态码（数字）
            # NetConnectionStatus 是 WMI 提供的属性，表示适配器的当前状态（2 表示已启用）

            enable = current_status != 2  # 2 表示已启用，所以如果当前状态不是 2，则启用
            action = "启用" if enable else "禁用"  # 根据 enable 变量决定执行启用还是禁用操作

            try:
                # 根据目标状态执行启用或禁用操作
                action_result = adapter.Enable() if enable else adapter.Disable()
                # Enable() 和 Disable() 是 WMI 提供的方法，用于启用或禁用网络适配器

                if isinstance(action_result, tuple) and action_result[0] == 0:
                    print(f"{action}网卡 '{adapter.Description}' 成功")  # 成功
                    return True, f"{adapter.Description} 已被成功{action}"
                else:
                    print(f"{action}网卡 '{adapter.Description}' 失败 - 返回值: {action_result}")
                    return False, f"{adapter.Description} {action}失败，返回值: {action_result}"

            except Exception as e:
                print(f"在尝试{action}网卡 '{adapter.Description}' 时发生错误: {e}")
                return False, f"{adapter.Description} {action}失败，错误: {str(e)}"

    except Exception as e:
        print(f"处理过程中发生了一个意外错误: {e}")  # 捕获其他异常
        return False, str(e)

def toggle_network_adapter_unix(adapter_name):
    """
    在 Linux 或 macOS 上切换指定网络适配器的状态。

    参数：
        adapter_name (str): 网络适配器的名称（如 eth0）

    返回值：
        Tuple[bool, str]: 
            - 成功与否的布尔值
            - 附加信息（成功或失败原因）
    """

    try:
        # 检查网卡是否存在
        check_cmd = f"ip link show {adapter_name}"
        if os.system(check_cmd) != 0:
            print(f"找不到名称为 '{adapter_name}' 的网络适配器")  # 未找到适配器
            return False, f"未找到名称为 {adapter_name} 的网卡"

        # 获取当前状态
        status_cmd = f"cat /sys/class/net/{adapter_name}/operstate"
        current_state = os.popen(status_cmd).read().strip()
        # os.popen() 执行命令并读取输出，strip() 去除首尾空白
        enable = current_state != 'up'  # 如果状态不是 'up'，则启用
        action = "启用" if enable else "禁用"

        print(f"当前网卡 '{adapter_name}' 状态为 {'已启用' if current_state == 'up' else '未启用'}")

        # 构造命令
        command = f"sudo ip link set dev {adapter_name} {'up' if enable else 'down'}"
        # sudo 是 Linux/macOS 中的权限提升命令，用于执行需要 root 权限的操作
        result_code = os.system(command)  # 执行命令

        if result_code == 0:
            print(f"{action}网卡 '{adapter_name}' 成功")
            return True, f"{adapter_name} 已被成功{action}"
        else:
            print(f"{action}网卡 '{adapter_name}' 失败")
            return False, f"{adapter_name} {action}失败，错误代码: {result_code}"

    except Exception as e:
        print(f"处理过程中发生了一个意外错误: {e}")  # 捕获其他异常
        return False, str(e)

def print_network_adapters_info(adapters):
    """
    打印所有网络适配器的信息，包括名称、IP、MAC 和状态。

    参数：
        adapters (List[Dict]): 由 list_network_adapters 返回的适配器列表

    返回值：
        None
    """

    for idx, adapter in enumerate(adapters, 1):
        print(f"\n网卡 {idx}:")  # 显示编号
        print(f"名称: {adapter['名称']}")  # 显示名称
        print(f"IP 地址: {adapter['IP']}")  # 显示 IP 地址
        print(f"MAC 地址: {adapter['MAC']}")  # 显示 MAC 地址
        print(f"状态: {adapter['状态']}")  # 显示当前状态

# ================= 主程序入口 ================= #

aaa = r'''


if __name__ == '__main__':
    """
    程序主入口，先打印所有网络适配器信息，然后切换指定网卡状态
    """

    # 列出所有网络适配器并打印
    adapters = list_network_adapters()
    print_network_adapters_info(adapters)

    # 示例：切换指定网卡状态（修改为你自己的网卡名称）
    network_adapter_name = "Realtek PCIe GbE Family Controller"  # 修改为你的网卡名称（Windows）或设备名（如 eth0）
    success, message = toggle_network_adapter(network_adapter_name)  # 切换状态

    # 输出操作结果
    print(f"\n操作结果: {success}, 详情: {message}")

    '''

toggle_network_adapter(bbb)
