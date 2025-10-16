import os
import subprocess
import locale
from typing import Tuple

def remove_files_safely(path: str = "123") -> Tuple[int, str, str]:
    """
    安全地删除指定路径下的文件或目录。
    
    参数:
        path (str): 要删除的文件或目录的路径，默认为"123"。
        
    返回值:
        Tuple[int, str, str]: (退出代码, 标准输出, 标准错误)。
    """
    # 检查提供的路径是否存在
    if not os.path.exists(path):
        #pass
        return -1, "", f"指定的路径 {path} 不存在。"

    # 构建删除命令
    command = ["del", '/S', '/F', '/Q', path]
    
    def execute_command(command) -> Tuple[int, str, str]:
        """
        在 shell 中执行命令，并返回退出代码、标准输出和标准错误。
        """
        print(f"运行的命令: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=False,
                check=False,
                shell=True,
            )
            
            def decode_with_fallback(byte_data):
                """尝试 UTF-8 解码，如果失败则使用系统默认编码解码"""
                if not byte_data:
                    return ""
                try:
                    return byte_data.decode('utf-8').strip()
                except UnicodeDecodeError:
                    sys_encoding = locale.getpreferredencoding()
                    return byte_data.decode(sys_encoding, errors='replace').strip()

            stdout = decode_with_fallback(result.stdout)
            stderr = decode_with_fallback(result.stderr)

            print(f"命令输出 (stdout):\n{stdout}")
            print(f"命令错误 (stderr):\n{stderr}" if stderr else "命令错误 (stderr): 无")

            return result.returncode, stdout, stderr

        except Exception as e:
            print(f"执行命令时发生异常: {str(e)}")
            return -1, "", str(e)

    # 执行删除命令
    return execute_command(command)
def execute_command(command) -> Tuple[int, str, str]:
    """
    在 shell 中执行命令，并返回退出代码、标准输出和标准错误。
    """
    print(f"运行的命令: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=False,
            check=False,
            shell=True,
        )
        
        def decode_with_fallback(byte_data):
            """尝试 UTF-8 解码，如果失败则使用系统默认编码解码"""
            if not byte_data:
                return ""
            try:
                return byte_data.decode('utf-8').strip()
            except UnicodeDecodeError:
                sys_encoding = locale.getpreferredencoding()
                return byte_data.decode(sys_encoding, errors='replace').strip()

        stdout = decode_with_fallback(result.stdout)
        stderr = decode_with_fallback(result.stderr)

        print(f"命令输出 (stdout):\n{stdout}")
        print(f"命令错误 (stderr):\n{stderr}" if stderr else "命令错误 (stderr): 无")

        return result.returncode, stdout, stderr

    except Exception as e:
        print(f"执行命令时发生异常: {str(e)}")
        return -1, "", str(e)

# 示例调用
if __name__ == "__main__":
    ret_code, stdout, stderr = remove_files_safely("123")
    #print(f"操作结果: 退出代码={ret_code}, 标准输出={stdout}, 标准错误={stderr}")