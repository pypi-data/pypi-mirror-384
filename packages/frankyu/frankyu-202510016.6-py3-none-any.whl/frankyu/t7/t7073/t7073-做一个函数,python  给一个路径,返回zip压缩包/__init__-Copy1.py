import os
import zipfile

def zip_folder(folder_path, output_zip=None):
    """
    将指定文件夹及其所有子文件夹和文件打包为 ZIP 文件。

    参数:
        folder_path (str): 要压缩的文件夹路径。
        output_zip (str, optional): 生成的 ZIP 文件路径。如果未提供，则默认使用文件夹名+.zip。

    返回:
        str: 生成的 ZIP 文件路径。
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"指定的路径不是一个有效的文件夹: {folder_path}")

    # 如果没有指定输出文件名，则用文件夹名+.zip
    if output_zip is None:
        folder_name = os.path.basename(os.path.abspath(folder_path))
        output_zip = os.path.join(os.path.dirname(folder_path), f"{folder_name}.zip")

    # 规范化路径（防止不同系统路径格式问题）
    folder_path = os.path.abspath(folder_path)

    print(f"开始压缩: {folder_path} -> {output_zip}")

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算相对路径，保证压缩包中的结构正确
                arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                zipf.write(file_path, arcname)

    print("压缩完成")
    return output_zip