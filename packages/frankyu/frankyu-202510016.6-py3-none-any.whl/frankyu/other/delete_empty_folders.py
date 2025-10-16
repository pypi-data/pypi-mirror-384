import os # 导入 os 模块，用于执行操作系统相关的任务，如文件和目录操作。

def delete_empty_folders(root_dir=r"./"):
    """
    递归删除指定路径下的所有空文件夹。
    这个函数会从最深的子目录开始检查并删除，
    确保父目录在其子目录被清理后也能被正确识别为空并删除。
    """
    # 首先，检查提供的根路径是否确实是一个有效的目录。
    if not os.path.isdir(root_dir):
        print(f"错误: '{root_dir}' 不是一个有效的目录。请检查路径。") # 如果不是目录，打印错误信息。
        return # 终止函数执行。

    print(f"正在扫描 '{root_dir}' 中的空文件夹...") # 告知用户扫描操作正在进行。
    deleted_count = 0 # 初始化一个计数器，用于记录删除的空文件夹数量。

    # 使用 os.walk() 遍历目录树。
    # dirpath: 当前访问的目录路径。
    # dirnames: 当前目录下的子目录名称列表。
    # filenames: 当前目录下的文件名称列表。
    # topdown=False 是关键：它指示 os.walk 从最深的子目录开始，然后向上遍历到父目录。
    # 这种“自下而上”的遍历顺序确保当一个子目录变空时，其父目录稍后也能被正确评估。
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        # 重新检查当前目录的内容。
        # 这一步很重要，因为在 os.walk 遍历过程中，一些子文件夹可能已经在之前的迭代中被删除了。
        # os.walk 返回的 dirnames 列表是遍历开始时的快照，可能不会实时更新。
        current_content = os.listdir(dirpath) # 获取当前目录的实际内容（文件和子目录的名称列表）。

        # 如果 'current_content' 为空列表，则表示当前目录是空的。
        if not current_content:
            try:
                # 尝试删除该空目录。
                # os.rmdir() 只能删除空目录；如果目录非空，它会抛出 OSError。
                os.rmdir(dirpath)
                print(f"已删除空文件夹: '{dirpath}'") # 成功删除后，打印提示信息。
                deleted_count += 1 # 增加已删除文件夹的计数。
            except OSError as e:
                # 捕获 OSError 异常。
                # 这类错误通常发生在以下情况：
                # 1. 目录在检查后但在删除前又被其他进程写入了内容（不再为空）。
                # 2. 脚本没有足够的权限来删除该目录。
                print(f"无法删除 '{dirpath}': {e}") # 打印删除失败的原因。
        # else:
        #     print(f"文件夹 '{dirpath}' 非空。") # 调试时可以取消注释，查看哪些文件夹是非空的。

    print(f"\n操作完成。共删除空文件夹: {deleted_count} 个。") # 打印最终的删除统计。


aaa = r'''

---

### 如何使用这个脚本（快速指南）

1.  **保存代码：** 将上述代码粘贴到一个文本文件，并将其保存为 `.py` 文件（例如 `clean_folders.py`）。
2.  **打开终端：** 启动你的命令提示符（Windows）或终端（macOS/Linux）。
3.  **运行脚本：** 使用 `python` 命令运行脚本，并在后面加上你希望清理的**目标文件夹路径**。

    **示例：**

    * **Windows:** `python clean_folders.py "C:\Users\YourUser\Downloads"`
    * **macOS/Linux:** `python clean_folders.py "/Users/YourUser/Documents/Temporary"`

    **提示：** 最好用**双引号**把路径括起来，以防路径中包含空格。

---

希望这些详细的注释能帮助你更好地理解和使用这个脚本！如果你对任何特定行或概念有进一步的疑问，请随时提出。


'''


if  __name__ == "__main__":
    delete_empty_folders()
    print(1)
    pass

