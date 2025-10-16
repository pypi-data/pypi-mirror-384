#!/usr/bin/env python
# coding: utf-8

# 导入系统信息模块 `system_info` 并重命名为 `sy`，用于调用其功能
import f_other.system_info as sy

# 调用 `get_username` 方法，传入参数 `1`，获取用户名并存储到变量 `name` 中
name = sy.get_username(1)

# 导入 `os` 模块，用于操作系统命令和功能
import os

# 使用 `os.system` 执行系统命令 `ping 127.1`
# 该命令用于向本地回环地址发送 ICMP 请求，测试网络堆栈是否正常工作
os.system("ping 127.1")