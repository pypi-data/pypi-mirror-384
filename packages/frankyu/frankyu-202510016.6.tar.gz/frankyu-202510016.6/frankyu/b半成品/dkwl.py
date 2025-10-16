import platform
import os
import sys
import wmi
import subprocess

def list_network_adapters():
    system_type = platform.system()
    if system_type == 'Windows':
        return list_network_adapters_windows()
    elif system_type in ['Linux', 'Darwin']:
        return list_network_adapters_unix()
    else:
        print("不支持的操作系统")
        return []

def list_network_adapters_windows():
    c = wmi.WMI()
    adapters = []
    for adapter in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
        ip_address = ', '.join(adapter.IPAddress) if adapter.IPAddress else '无'
        mac_address = adapter.MACAddress if adapter.MACAddress else '无'
        status = '已启用' if adapter.IPEnabled else '未启用'
        description = adapter.Description
        adapters.append({
            '名称': description,
            'IP': ip_address,
            'MAC': mac_address,
            '状态': status
        })
    return adapters

def list_network_adapters_unix():
    result = subprocess.run(['ip', '-o', '-br', 'addr', 'show'], stdout=subprocess.PIPE)
    lines = result.stdout.decode().splitlines()
    adapters = []
    for line in lines:
        parts = line.split()
        name = parts[0]
        ips = [part.split('/')[0] for part in parts[2:] if part != 'inet' and part != 'inet6']
        ip_address = ', '.join(ips) if ips else '无'
        
        mac_result = subprocess.run(['cat', '/sys/class/net/{}/address'.format(name)], stdout=subprocess.PIPE)
        mac_address = mac_result.stdout.decode().strip() if mac_result.returncode == 0 else '无'
        
        status_result = subprocess.run(['cat', '/sys/class/net/{}/operstate'.format(name)], stdout=subprocess.PIPE)
        status = status_result.stdout.decode().strip() if status_result.returncode == 0 else '未知'
        
        adapters.append({
            '名称': name,
            'IP': ip_address,
            'MAC': mac_address,
            '状态': status
        })
    return adapters

def toggle_network_adapter(adapter_name):
    system_type = platform.system()
    if system_type == 'Windows':
        success, message = toggle_network_adapter_windows(adapter_name)
    elif system_type in ['Linux', 'Darwin']:
        success, message = toggle_network_adapter_unix(adapter_name)
    else:
        print("不支持的操作系统")
        return False, "不支持的操作系统"
    
    return success, message

# Windows-specific function to toggle network adapter state
def toggle_network_adapter_windows(adapter_name):
    try:
        c = wmi.WMI()
        adapters = c.Win32_NetworkAdapter(Description=adapter_name)
        if not adapters:
            print(f"找不到描述为 '{adapter_name}' 的网络适配器")
            return False, f"未找到名称为 {adapter_name} 的网卡"

        for adapter in adapters:
            current_status = adapter.NetConnectionStatus
            enable = current_status != 2  # 2 表示连接状态
            action = "启用" if enable else "禁用"
            
            try:
                action_result = adapter.Enable() if enable else adapter.Disable()
                if isinstance(action_result, tuple) and action_result[0] == 0:
                    print(f"{action}网卡 '{adapter.Description}' 成功")
                    return True, f"{adapter.Description} 已被成功{action}"
                else:
                    print(f"{action}网卡 '{adapter.Description}' 失败 - 返回值: {action_result}")
                    return False, f"{adapter.Description} {action}失败，返回值: {action_result}"
            except Exception as e:
                print(f"在尝试{action}网卡 '{adapter.Description}' 时发生错误: {e}")
                return False, f"{adapter.Description} {action}失败，错误: {str(e)}"
                
    except Exception as e:
        print(f"处理过程中发生了一个意外错误: {e}")
        return False, str(e)

# Linux/macOS-specific function to toggle network adapter state
def toggle_network_adapter_unix(adapter_name):
    try:
        check_cmd = f"ip link show {adapter_name}"
        if os.system(check_cmd) != 0:
            print(f"找不到名称为 '{adapter_name}' 的网络适配器")
            return False, f"未找到名称为 {adapter_name} 的网卡"

        status_cmd = f"cat /sys/class/net/{adapter_name}/operstate"
        current_state = os.popen(status_cmd).read().strip()
        enable = current_state != 'up'
        action = "启用" if enable else "禁用"

        print(f"当前网卡 '{adapter_name}' 状态为 {'已启用' if current_state == 'up' else '未启用'}")

        command = f"sudo ip link set dev {adapter_name} {'up' if enable else 'down'}"
        result_code = os.system(command)
        
        if result_code == 0:
            print(f"{action}网卡 '{adapter_name}' 成功")
            return True, f"{adapter_name} 已被成功{action}"
        else:
            print(f"{action}网卡 '{adapter_name}' 失败")
            return False, f"{adapter_name} {action}失败，错误代码: {result_code}"
    except Exception as e:
        print(f"处理过程中发生了一个意外错误: {e}")
        return False, str(e)

# 打印所有网络适配器的信息
def print_network_adapters_info(adapters):
    for idx, adapter in enumerate(adapters, 1):
        print(f"\n网卡 {idx}:")
        print(f"名称: {adapter['名称']}")
        print(f"IP 地址: {adapter['IP']}")
        print(f"MAC 地址: {adapter['MAC']}")
        print(f"状态: {adapter['状态']}")

# 示例调用
adapters = list_network_adapters()
print_network_adapters_info(adapters)

network_adapter_name = "Realtek RTL8852BE WiFi 6 802.11ax PCIe Adapter"  # 修改为你的网卡名称
success, message = toggle_network_adapter(network_adapter_name)
print(f"\n操作结果: {success}, 详情: {message}")