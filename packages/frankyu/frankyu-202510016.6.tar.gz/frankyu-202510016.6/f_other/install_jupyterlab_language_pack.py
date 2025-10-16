import os
# 导入 os 模块，用于操作文件和路径，比如检查文件是否存在

import shutil
# 导入 shutil 模块，用于高级文件操作，比如查找系统路径中的可执行文件

import subprocess
# 导入 subprocess 模块，用于运行外部命令并捕获其输出

from typing import Optional, Tuple
# 从 typing 模块导入 Optional 和 Tuple，用于函数的返回值类型提示

from packaging import version as version_parser
# 从 packaging.version 模块导入 version 并重命名为 version_parser，用于处理和比较版本号


def get_pip_location(default_pip_path='C:\\anaconda3\\Scripts\\pip.EXE', prefer_default_pip=0) -> Optional[str]:
    # 定义函数 get_pip_location，用于获取 pip 可执行文件的位置
    """
    获取 pip 可执行文件的位置。

    思路:
        1. 如果用户指定默认 pip 路径且优先使用该路径，则检查路径是否存在。
        2. 尝试通过自定义模块 `f_other.system_info` 获取 pip 路径。
        3. 使用 `shutil.which("pip")` 检查环境变量中的 pip 位置。
        4. 如果上述方法都失败，则返回默认路径（如果存在），否则返回 None。

    方法清单:
    - os.path.exists(): 检查路径是否存在。
    - shutil.which("pip"): 查找环境变量中的 pip 可执行文件。
    - f_other.system_info.get_pip_location(): 自定义方法获取 pip 路径。

    参数:
        default_pip_path (str): 默认 pip 路径。
        prefer_default_pip (bool): 是否优先使用默认路径。

    返回值:
        Optional[str]: pip 的可执行文件路径，或 None（如果找不到）。
    """
    if prefer_default_pip and os.path.exists(default_pip_path):
        # 如果 prefer_default_pip 为真且指定路径存在，则优先返回默认 pip 路径
        return default_pip_path
    
    try:
        import f_other.system_info
        # 尝试导入自定义模块 f_other.system_info，用于获取 pip 路径
        return f_other.system_info.get_pip_location()
        # 调用自定义模块的方法获取 pip 路径
    except ImportError:
        # 如果模块不存在或导入失败，捕获 ImportError 并继续执行后续逻辑
        pass
    
    # 使用 shutil.which("pip") 在系统环境变量中查找 pip 可执行文件
    # 如果找不到 pip，则检查默认路径是否存在，最终返回 None 或找到的路径
    return shutil.which("pip") or (default_pip_path if os.path.exists(default_pip_path) else None)


def execute_command(command=["ipconfig"]) -> Tuple[int, str, str]:
    # 定义函数 execute_command，用于在 shell 中执行命令并返回结果
    """
    在 shell 中执行命令，并返回退出代码、标准输出和标准错误。

    思路:
        1. 使用 subprocess.run 捕获命令输出。
        2. 优先尝试 UTF-8 解码，失败时使用系统默认编码。
        3. 捕获命令的标准输出和错误。

    方法清单:
    - subprocess.run(): 执行 shell 命令。
    - decode(): 解码命令输出的字节数据。

    参数:
        command (list): 要执行的命令列表。

    返回值:
        Tuple[int, str, str]: (退出代码, 标准输出, 标准错误)。
    """
    print(f"运行的命令: {' '.join(command)}")
    # 打印要运行的命令，方便调试

    try:
        # 调用 subprocess.run 捕获命令的输出
        result = subprocess.run(
            command,
            capture_output=True,  # 捕获标准输出和标准错误
            text=False,  # 返回字节数据，而不是字符串
            check=False  # 不抛出运行时错误
        )
        
        def decode_with_fallback(byte_data):
            # 定义一个解码函数，优先尝试 UTF-8 解码，失败则回退到系统默认编码
            if not byte_data:
                # 如果输入为空字节数据，返回空字符串
                return ""
            try:
                return byte_data.decode('utf-8').strip()
                # 尝试使用 UTF-8 解码，并去除首尾空格
            except UnicodeDecodeError:
                # 如果 UTF-8 解码失败，尝试使用系统默认编码
                sys_encoding = locale.getpreferredencoding()
                return byte_data.decode(sys_encoding, errors='replace').strip()
        
        stdout = decode_with_fallback(result.stdout)
        # 解码标准输出

        stderr = decode_with_fallback(result.stderr)
        # 解码标准错误

        print(f"命令输出 (stdout):\n{stdout}")
        # 打印标准输出

        print(f"命令错误 (stderr):\n{stderr}" if stderr else "命令错误 (stderr): 无")
        # 打印标准错误，如果没有错误，则打印“无”

        return result.returncode, stdout, stderr
        # 返回退出代码、标准输出和标准错误

    except Exception as e:
        # 捕获运行命令时的所有异常
        print(f"执行命令时发生异常: {str(e)}")
        # 打印异常信息
        return -1, "", str(e)
        # 返回 -1 表示失败，同时返回空的标准输出和错误信息


def check_package_version(package_name: str, mirror_url: Optional[str] = None, pip_location: str = r"C:\anaconda3\Scripts\pip.exe") -> Optional[str]:
    # 定义函数 check_package_version，用于检查指定包的安装版本
    """
    检查指定包的安装版本。

    思路:
        1. 构建 pip show 命令来获取包信息。
        2. 如果成功获取信息，则提取版本号。

    方法清单:
    - pip show: 获取已安装包的信息。
    - str.startswith(): 检查行是否包含 "version:"。

    参数:
        package_name (str): 包名。
        mirror_url (Optional[str]): 可选的镜像 URL。
        pip_location (str): pip 的路径。

    返回值:
        Optional[str]: 返回包的安装版本，或 None。
    """
    if not package_name.strip():
        # 如果包名为空，返回 None
        return None

    command = [pip_location, "show", package_name]
    # 构建 pip show 命令，用于获取包的详细信息

    if mirror_url:
        # 如果提供了镜像 URL，扩展命令以包含镜像参数
        pass

    exit_code, stdout, _ = execute_command(command)
    # 调用 execute_command 执行命令，获取退出代码和标准输出

    if exit_code == 0:
        # 如果命令执行成功
        for line in stdout.splitlines():
            # 遍历命令输出的每一行
            if line.lower().startswith("version:"):
                # 如果找到以 version: 开头的行
                return line.split(":", 1)[1].strip()
                # 提取版本号并返回

    return None
    # 如果未成功获取版本信息，返回 None


def uninstall_package(package_name: str = "xlwings", pip_location: str = r"C:\anaconda3\Scripts\pip.exe") -> str:
    # 定义函数 uninstall_package，用于卸载指定的 Python 包
    """
    卸载指定的 Python 包。

    思路:
        1. 检查包是否已安装，未安装则返回提示。
        2. 构建 pip uninstall 命令。
        3. 执行命令并返回结果。

    方法清单:
    - pip uninstall: 卸载包。
    - execute_command(): 执行命令。

    参数:
        package_name (str): 包名。
        pip_location (str): pip 的路径。

    返回值:
        str: 卸载结果信息。
    """
    if not package_name.strip():
        # 如果包名为空，返回错误信息
        return "卸载失败：包名不能为空。"

    installed_version = check_package_version(package_name, None, pip_location)
    # 检查包的已安装版本

    if not installed_version:
        # 如果包未安装，返回提示信息
        return f"包 {package_name} 未安装，无需卸载。"

    command = [pip_location, "uninstall", "-y", package_name]
    # 构建 pip uninstall 命令

    exit_code, _, stderr = execute_command(command)
    # 执行命令并捕获退出代码和错误信息

    if exit_code == 0:
        # 如果命令执行成功
        return f"卸载成功：包名 {package_name}, 版本 {installed_version}"

    return f"卸载失败。错误信息:\n{stderr}"
    # 如果卸载失败，返回错误信息


def install_package_with_version_check(
    package_name: str = "jupyterlab-language-pack-zh-CN",
    default_pip_path: str = r"C:\anaconda3\Scripts\pip.exe",
    mirror_url: Optional[str] = r"https://pypi.tuna.tsinghua.edu.cn/simple",
    prefer_default_pip: bool = True
) -> str:
    # 定义函数 install_package_with_version_check，用于安装或升级指定的 Python 包
    """
    安装或升级指定的 Python 包，并检查版本变化。

    思路:
        1. 获取 pip 路径。
        2. 检查安装前的包版本。
        3. 执行 pip install 命令。
        4. 检查安装后的包版本。

    方法清单:
    - pip install: 安装或升级包。
    - check_package_version(): 获取包的版本信息。

    参数:
        package_name (str): 包名。
        default_pip_path (str): 默认 pip 路径。
        mirror_url (Optional[str]): 镜像 URL。
        prefer_default_pip (bool): 是否优先使用默认 pip。

    返回值:
        str: 包含安装前后版本信息的字符串。
    """
    if not package_name.strip():
        # 如果包名为空，返回错误信息
        return "操作失败：包名不能为空。"

    pip_location = get_pip_location(default_pip_path, prefer_default_pip)
    # 获取 pip 的实际路径

    if not pip_location:
        # 如果未找到 pip，返回错误信息
        return "找不到 pip 可执行文件，无法操作包。"

    installed_version = check_package_version(package_name, None, pip_location)
    # 获取包的已安装版本

    print(f"已安装版本: {installed_version if installed_version else '未安装'}")
    # 打印已安装版本信息

    command = [pip_location, "install", package_name]
    # 构建 pip install 命令

    if mirror_url:
        # 如果提供了镜像 URL，扩展命令以包含镜像参数
        command.extend(["-i", mirror_url])

    execute_command(command)
    # 执行安装命令

    new_version = check_package_version(package_name, None, pip_location)
    # 获取安装后的包版本

    return f"已安装版本: {installed_version}, 安装后版本: {new_version}"
    # 返回版本变化信息


if __name__ == "__main__":
    # 如果当前脚本作为主程序运行
    package_name = "frankyu"
    # 设置要操作的包名

    default_pip_path = r"C:\anaconda3\Scripts\pip.exe"
    # 设置默认 pip 路径

    pip_location = get_pip_location(default_pip_path, prefer_default_pip=True)
    # 获取 pip 的实际路径

    if pip_location:
        # 如果找到了 pip，尝试卸载包
        uninstall_result = uninstall_package(package_name, pip_location)
        print(uninstall_result)
    else:
        # 如果未找到 pip，打印提示信息
        print("找不到 pip 可执行文件，无法卸载包。")