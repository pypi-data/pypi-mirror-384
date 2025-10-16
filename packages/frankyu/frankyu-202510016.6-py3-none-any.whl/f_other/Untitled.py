#!/usr/bin/env python
# coding: utf-8

# 导入 `install_jupyterlab_language_pack` 模块，并重命名为 `ins`，方便后续调用其方法
import f_other.install_jupyterlab_language_pack as ins

# 调用 `check_package_version` 方法，检查 `frankyu` 包的当前版本
# 提供 pip 的路径为 `C:\Users\Public\Python314\Scripts\pip.exe`
ins.check_package_version("frankyu", pip_location=r"C:\Users\Public\Python314\Scripts\pip.exe")

# 调用 `execute_command` 方法，使用 pip 命令升级 `frankyu` 包至最新版本
# pip 的路径为 `C:\Users\Public\Python314\Scripts\pip.exe`
ins.execute_command([
    r"C:\Users\Public\Python314\Scripts\pip.exe",  # pip 可执行文件路径
    "install",  # pip 的子命令，表示安装或升级包
    "--upgrade",  # 升级选项
    "frankyu"  # 要安装或升级的包名
])

# 输出模块 `ins`，通常用于检查模块是否正确加载
ins