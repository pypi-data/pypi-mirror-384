import os
import shutil
import subprocess
from typing import Optional, Tuple
from packaging import version as version_parser


# 假设的 execute_command 函数，可能包含打印语句
def execute_command(command: list) -> Tuple[int, str, str]:
    try:
        # 这里是假设的打印输出，您可以在此进行修改
        # print(f"Executing command: {' '.join(command)}") # 假设的打印语句

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8' # 指定编码以避免乱码
        )
        stdout, stderr = process.communicate()
        exit_code = process.returncode

        # 假设的错误打印语句
        # if exit_code != 0:
        #     print(f"Error executing command: {stderr}")

        return exit_code, stdout, stderr
    except Exception as e:
        # print(f"Exception during command execution: {e}") # 假设的异常打印语句
        return -1, "", str(e)


def check_package_version(package_name: str, mirror_url: Optional[str] = None, pip_location: str = r"C:\anaconda3\Scripts\pip.exe", printf=0) -> Optional[str]:
    if not package_name.strip():
        return None

    command = [pip_location, "show", package_name]

    if mirror_url:
        pass

    exit_code, stdout, _ = execute_command(command)

    if exit_code == 0:
        for line in stdout.splitlines():
            if line.lower().startswith("version:"):
                return line.split(":", 1)[1].strip()

    return None