import os
import zipfile
import shutil
import re
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

# 页面设置
st.set_page_config(page_title="ZIP解压工具", page_icon="📦", layout="wide")

def safe_extract(zip_ref, extract_path, overwrite=False):
    """安全解压文件，处理各种异常情况"""
    extracted_files = []
    skipped_files = []
    
    for file in zip_ref.namelist():
        try:
            # 处理路径安全问题
            dest_path = os.path.join(extract_path, file)
            if not dest_path.startswith(extract_path):
                raise ValueError("非法路径")
                
            if os.path.exists(dest_path) and not overwrite:
                skipped_files.append(file)
                continue
                
            zip_ref.extract(file, extract_path)
            extracted_files.append(file)
        except Exception as e:
            st.warning(f"解压失败 {file}: {str(e)}")
    
    return extracted_files, skipped_files

def process_zip(uploaded_file: UploadedFile, extract_path, overwrite=False):
    """处理上传的ZIP文件"""
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            # 显示ZIP内容
            with st.expander("📂 查看ZIP文件内容"):
                file_list = zip_ref.namelist()
                st.write(f"包含 {len(file_list)} 个文件:")
                st.dataframe(
                    sorted(file_list),
                    height=200,
                    column_config={"value": "文件名"},
                    hide_index=True
                )
            
            # 执行解压
            extracted, skipped = safe_extract(zip_ref, extract_path, overwrite)
            
            # 显示结果
            st.success(f"成功解压 {len(extracted)} 个文件到: {extract_path}")
            if skipped:
                st.warning(f"跳过 {len(skipped)} 个已存在文件 (启用覆盖选项可强制解压)")
            
            # 特殊文件检测
            ipynb_files = [f for f in extracted if f.lower().endswith('.ipynb')]
            if ipynb_files:
                st.info(f"检测到 {len(ipynb_files)} 个Jupyter笔记本文件")
                for f in ipynb_files[:3]:  # 最多显示3个
                    st.code(os.path.join(extract_path, f), language="python")
    
    except zipfile.BadZipFile:
        st.error("错误: 不是有效的ZIP文件")
    except Exception as e:
        st.error(f"解压失败: {str(e)}")

def main():
    st.title("📦 ZIP文件解压工具")
    st.markdown("上传ZIP文件或处理目录中的ZIP文件")
    
    # 创建两列布局
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("配置选项")
        
        # 解压模式选择
        mode = st.radio(
            "选择操作模式",
            ["上传ZIP文件", "处理目录中的ZIP"],
            horizontal=True
        )
        
        # 通用选项
        overwrite = st.checkbox("覆盖已存在文件", False)
        create_subdir = st.checkbox("为每个ZIP创建单独目录", True)
        
        if mode == "处理目录中的ZIP":
            target_dir = st.text_input(
                "目标目录路径",
                value="~/360a",
                help="支持Linux路径格式，如 ~/downloads"
            )
        else:
            uploaded_files = st.file_uploader(
                "选择ZIP文件",
                type=['zip'],
                accept_multiple_files=True
            )
    
    with col2:
        st.subheader("操作面板")
        
        if mode == "处理目录中的ZIP":
            if st.button("开始解压目录中的ZIP文件"):
                target_dir = os.path.expanduser(target_dir)
                if not os.path.exists(target_dir):
                    st.error(f"目录不存在: {target_dir}")
                    return
                
                zip_files = [f for f in os.listdir(target_dir) 
                            if f.lower().endswith('.zip')]
                
                if not zip_files:
                    st.warning("目标目录中没有找到ZIP文件")
                    return
                
                progress_bar = st.progress(0)
                for i, zip_file in enumerate(zip_files):
                    progress = (i + 1) / len(zip_files)
                    progress_bar.progress(progress)
                    
                    zip_path = os.path.join(target_dir, zip_file)
                    extract_dir = re.sub(r'\.zip$', '', zip_file, flags=re.IGNORECASE)
                    
                    if create_subdir:
                        extract_path = os.path.join(target_dir, extract_dir)
                        os.makedirs(extract_path, exist_ok=True)
                    else:
                        extract_path = target_dir
                    
                    with st.status(f"正在处理 {zip_file}...", expanded=True):
                        try:
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                extracted, skipped = safe_extract(
                                    zip_ref, extract_path, overwrite)
                                
                                st.write(f"解压 {len(extracted)} 个文件")
                                if skipped:
                                    st.write(f"跳过 {len(skipped)} 个文件")
                        except Exception as e:
                            st.error(f"处理失败: {str(e)}")
                
                st.success(f"完成处理 {len(zip_files)} 个ZIP文件")
                progress_bar.empty()
        
        else:  # 上传模式
            if uploaded_files and st.button("开始解压上传的文件"):
                for uploaded_file in uploaded_files:
                    with st.expander(f"处理 {uploaded_file.name}", expanded=True):
                        extract_dir = re.sub(r'\.zip$', '', uploaded_file.name, 
                                           flags=re.IGNORECASE)
                        
                        if create_subdir:
                            extract_path = os.path.join(os.getcwd(), extract_dir)
                            os.makedirs(extract_path, exist_ok=True)
                        else:
                            extract_path = os.getcwd()
                        
                        process_zip(uploaded_file, extract_path, overwrite)
    
    # 添加使用说明
    with st.expander("ℹ️ 使用说明"):
        st.markdown("""
        ### 功能说明
        1. **上传模式**：直接上传ZIP文件进行解压
        2. **目录模式**：处理指定目录中的所有ZIP文件
        
        ### 选项说明
        - **覆盖文件**：当目标文件已存在时覆盖
        - **创建子目录**：为每个ZIP文件创建单独的解压目录
        
        ### 注意事项
        - 支持大文件解压（自动流式处理）
        - 自动处理中文文件名
        - 显示详细的解压过程日志
        """)

if __name__ == "__main__":
    main()