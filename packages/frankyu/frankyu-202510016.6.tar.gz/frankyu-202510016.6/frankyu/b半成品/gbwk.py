import wmi

# 连接到WMI
c = wmi.WMI()

# 网卡的名字
network_adapter_name = "Realtek PCIe GbE Family Controller"

# 查找匹配的网络适配器
for adapter in c.Win32_NetworkAdapter(Description=network_adapter_name):
    # 打印一些信息，确保找到了正确的适配器
    print(f"找到网卡: {adapter.Description}, 状态: {adapter.NetConnectionStatus}")

    # 尝试禁用网络适配器
    try:
        result = adapter.Disable()
        if result == (0,):
            print("网卡已成功禁用")
        else:
            print("禁用网卡失败")
    except Exception as e:
        print(f"发生错误: {e}")