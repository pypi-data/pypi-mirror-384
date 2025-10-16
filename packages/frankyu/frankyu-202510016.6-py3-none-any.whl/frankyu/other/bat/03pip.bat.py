import subprocess
import os

def run_command(command):
    """运行一个 shell 命令并打印输出。"""
    try:
        process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(process.stdout)
        if process.stderr:
            print(process.stderr)
    except subprocess.CalledProcessError as e:
        print(f"执行命令 '{command}' 时发生错误: {e}")
    except FileNotFoundError:
        print(f"错误: 未找到命令 '{command.split()[0]}'.")

# 执行 ping 命令
print("正在执行 ping 127.1...")
run_command("ping 127.1")
run_command("ping 127.1")

# 构建软件包
#print("\n开始构建软件包...")
#run_command("python setup.py sdist bdist_wheel")

# 安装 twine (如果尚未安装，我们将尝试运行它)
#print("\n检查并安装 twine...")
#try:
    #subprocess.run(['twine', '--version'], check=True, capture_output=True)
    #print("twine 已经安装或可在您的 PATH 中访问。")
#except subprocess.CalledProcessError:
    #print("twine 未安装。正在安装...")
    #run_command("pip install twine")

# 使用 twine 上传软件包
#print("\n使用 twine 上传软件包...")
# 强烈建议不要在脚本中硬编码您的 PyPI 凭据。
# 相反，您应该使用环境变量 (TWINE_USERNAME, TWINE_PASSWORD)
# 或通过在您的主目录中创建一个 .pypirc 文件来配置 twine。
# 有关更多详细信息，请参阅 twine 文档：https://twine.readthedocs.io/en/latest/
#
# 下面的命令展示了如何直接包含凭据，但这不安全。
# run_command(f"twine upload --username your_pypi_username --password pypi-AgEIcHlwaS5vcmcCJDM4NzZiNDMwLTRlOGYtNGEyZS1iZDUxLTM4N2FiMTNkNmNhMwACKlszLCJhZWE0NGMxZS1lNjBkLTQ1ZTYtODdlNC1lNjkzZWFkMjc1YjciXQAABiDiu6I3LqNTXvIRmiB_eMNpvZksRz8gY0UwbipwH6fHIg dist/*")

# 更安全的方法是依赖环境变量或 .pypirc 文件：
#run_command("twine upload dist/*")

# 使用 pip 的完整路径卸载 frankyu
#print("\n卸载 frankyu...")
pip_executable = r"pip.exe"
#if os.path.exists(pip_executable):
#    run_command(f'"{pip_executable}" uninstall frankyu -y')
#else:
#    print(f"警告: 在 '{pip_executable}' 未找到 pip 可执行文件。跳过卸载。")

# 使用 pip 安装并升级 frankyu
print("\n安装并升级 frankyu...")
if 1:
    run_command(f'"{pip_executable}" install --upgrade frankyu')
else:
    print(f"警告: 在 '{pip_executable}' 未找到 pip 可执行文件。跳过安装。")

# 模拟 pause 命令
input("\n按 Enter 键继续...")