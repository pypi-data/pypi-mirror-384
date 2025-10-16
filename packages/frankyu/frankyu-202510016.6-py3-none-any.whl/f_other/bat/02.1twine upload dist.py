import subprocess  # 导入 subprocess 模块，用于运行外部命令
import os  # 导入 os 模块，用于进行操作系统相关的操作，例如检查文件是否存在

def run_command(command):
    """运行一个 shell 命令并打印输出。"""
    try:
        process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(process.stdout)  # 打印命令的标准输出
        if process.stderr:
            print(process.stderr)  # 如果有错误，打印命令的标准错误输出
    except subprocess.CalledProcessError as e:
        print(f"执行命令 '{command}' 时发生错误: {e}")  # 捕获命令执行错误并打印
    except FileNotFoundError:
        print(f"错误: 未找到命令 '{command.split()[0]}'.")  # 捕获命令未找到的错误并打印

# 构建软件包
#run_command("python setup.py sdist bdist_wheel")  # 运行命令来创建源代码分发包和 wheel 文件

# 安装 twine (如果尚未安装，我们将尝试运行它)
print("\n尝试使用 twine 上传...")
try:
    subprocess.run(['twine', '--version'], check=True, capture_output=True)
    print("twine 已经安装或可在您的 PATH 中访问。")
except subprocess.CalledProcessError:
    print("twine 未安装。正在安装...")
    run_command("pip install twine")  # 运行命令来安装 twine

# 使用 twine 上传软件包
print("\n正在使用 twine 上传软件包...")
# 强烈建议不要在脚本中硬编码您的 PyPI 凭据。
# 相反，您应该使用环境变量 (TWINE_USERNAME, TWINE_PASSWORD)
# 或通过在您的主目录中创建一个 .pypirc 文件来配置 twine。
# 有关更多详细信息，请参阅 twine 文档：https://twine.readthedocs.io/en/latest/
#
# 下面的命令展示了如何直接包含凭据，但这不安全。
# run_command(f"twine upload --username your_pypi_username --password pypi-AgEIcHlwaS5vcmcCJDM4NzZiNDMwLTRlOGYtNGEyZS1iZDUxLTM4N2FiMTNkNmNhMwACKlszLCJhZWE0NGMxZS1lNjBkLTQ1ZTYtODdlNC1lNjkzZWFkMjc1YjciXQAABiDiu6I3LqNTXvIRmiB_eMNpvZksRz8gY0UwbipwH6fHIg dist/*")

# 更安全的方法是依赖环境变量或 .pypirc 文件：
run_command("twine upload dist/*")  # 运行命令来上传软件包

# 模拟 pause 命令
#input("\n按 Enter 键继续...")  # 提示用户按 Enter 键继续