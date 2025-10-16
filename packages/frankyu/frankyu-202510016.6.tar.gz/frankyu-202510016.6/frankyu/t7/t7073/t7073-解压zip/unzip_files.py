import os
import zipfile
import shutil
import re

def unzip_files(target_dir=None, overwrite=False, create_subdir=True):
    """
    解压当前目录或指定目录中的所有ZIP文件
    
    参数:
    target_dir (str): 要处理的目录路径（默认为当前目录）
    overwrite (bool): 是否覆盖已存在的解压文件（默认False）
    create_subdir (bool): 是否为每个ZIP创建单独的子目录（默认True）
    """
    # 设置目标目录
    target_dir = os.path.expanduser(target_dir or '~')
    os.chdir(target_dir)
    
    print(f"处理目录: {os.getcwd()}")
    print(f"找到文件: {os.listdir()}")
    
    # 查找所有ZIP文件
    zip_files = [f for f in os.listdir() if f.lower().endswith('.zip')]
    
    if not zip_files:
        print("未找到ZIP文件")
        return
    
    for zip_file in zip_files:
        print(f"\n处理文件: {zip_file}")
        
        try:
            # 创建解压目录
            extract_dir = re.sub(r'\.zip$', '', zip_file, flags=re.IGNORECASE)
            if create_subdir:
                os.makedirs(extract_dir, exist_ok=True)
                extract_path = extract_dir
            else:
                extract_path = '.'
            
            # 解压文件
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # 检查是否已存在文件
                existing_files = []
                for file in file_list:
                    dest_path = os.path.join(extract_path, file)
                    if os.path.exists(dest_path):
                        existing_files.append(file)
                
                if existing_files and not overwrite:
                    print(f"! 跳过解压 (存在 {len(existing_files)} 个已存在的文件)")
                    print(f"  使用 overwrite=True 参数覆盖文件")
                    print(f"  冲突文件示例: {existing_files[:3]}")
                    continue
                
                print(f"解压 {len(file_list)} 个文件到 {extract_path}...")
                zip_ref.extractall(extract_path)
                print(f"✓ 解压完成")
                
                # 检查特殊文件
                ipynb_files = [f for f in file_list if f.lower().endswith('.ipynb')]
                if ipynb_files:
                    print(f"  包含Jupyter笔记本: {ipynb_files}")
        
        except zipfile.BadZipFile:
            print(f"× 错误: {zip_file} 不是有效的ZIP文件")
        except PermissionError:
            print(f"× 错误: 没有权限解压 {zip_file}")
        except Exception as e:
            print(f"× 解压失败: {str(e)}")

# 使用示例 (根据你的路径调整)
if __name__ == "__main__":
    # 解压~/360a目录下的ZIP文件
    unzip_files('~/360a')
    
    # 可选参数示例:
    # unzip_files('~/360a', overwrite=T