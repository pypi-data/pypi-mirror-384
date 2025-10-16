import subprocess

# 执行 python setup.py sdist bdist_wheel
try:
    subprocess.run(['python', 'setup.py', 'sdist', 'bdist_wheel'], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error executing the setup command: {e}")

# 模拟 pause 命令
input("Press Enter to continue...")