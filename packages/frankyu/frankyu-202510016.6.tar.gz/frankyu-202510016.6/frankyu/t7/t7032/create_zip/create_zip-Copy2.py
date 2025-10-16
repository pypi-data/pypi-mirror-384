import streamlit as st # 导入 Streamlit 库，用于构建 Web 应用
import os # 导入 os 模块，用于操作系统相关功能，如路径操作
from io import BytesIO # 从 io 模块导入 BytesIO，用于在内存中处理二进制数据流
import datetime # 导入 datetime 模块，用于处理日期和时间

# --- 导入错误处理 ---
try: # 尝试执行代码块
    import zipfile # 导入 zipfile 模块，用于创建和读取 ZIP 压缩文件
except ImportError: # 如果 zipfile 模块导入失败（例如，未安装）
    st.error("错误：缺少 'zipfile' 模块。") # 在 Streamlit 界面显示错误信息
    st.error("请确保您的 Python 环境中已安装 'zipfile'。") # 提供解决方案
    st.stop() # 停止 Streamlit 应用的进一步执行，防止后续错误

def create_zip(files):
    """
    将文件列表打包成ZIP文件。
    增加错误处理，例如空文件列表或写入失败。
    """
    if not files: # 检查传入的文件列表是否为空
        st.warning("没有文件可供打包。") # 如果没有文件，显示警告信息
        return None # 返回 None，表示没有成功创建ZIP文件

    zip_buffer = BytesIO() # 创建一个 BytesIO 对象，作为 ZIP 文件的内存缓冲区
    try: # 尝试执行 ZIP 文件创建和写入操作
        with zipfile.ZipFile(zip_buffer, # 指定 ZIP 文件的写入目标是这个内存缓冲区
                             "a", # 模式："a" 表示追加写入，如果文件不存在则创建
                             zipfile.ZIP_DEFLATED, # 压缩方法：使用 DEFLATE 算法进行压缩
                             False) as zip_file: # 是否支持 Zip64 扩展：False 表示不支持（通常用于小文件）
            for uploaded_file in files: # 遍历用户上传的每一个文件
                try: # 尝试将当前文件写入 ZIP 压缩包
                    # 获取原始文件名
                    file_name = os.path.basename( # 使用 os.path.basename 获取文件在原始路径中的基本名称（不含路径）
                        uploaded_file.name) # uploaded_file.name 是上传文件的原始文件名
                    file_content = uploaded_file.getvalue() # 获取上传文件的二进制内容
                    zip_file.writestr(file_name, # 将文件内容写入 ZIP 压缩包，使用其原始文件名
                                      file_content) # 要写入的文件内容
                except Exception as e: # 如果单个文件写入失败，捕获所有异常
                    st.error(f"写入文件 '{file_name}' 失败: {e}") # 显示具体的文件名和错误信息
                    return None # 如果单个文件写入失败，立即停止打包并返回 None
        zip_buffer.seek(0) # 将内存缓冲区的指针重置到开头（0），以便后续读取
        return zip_buffer # 返回包含 ZIP 文件内容的内存缓冲区
    except Exception as e: # 如果在创建 ZIP 压缩包时发生任何其他意外错误
        st.error(f"创建 ZIP 压缩包时出错: {e}") # 显示创建 ZIP 时的通用错误信息
        return None # 返回 None，表示 ZIP 文件生成失败

# --- Streamlit 应用界面 ---
st.set_page_config(page_title="文件压缩下载工具", # 设置浏览器标签页的标题
                   layout="centered") # 设置页面布局为居中模式

st.title("文件压缩下载工具") # 在网页上显示主标题
st.write("上传文件，生成含时间戳的ZIP压缩包。") # 显示应用的功能说明

uploaded_files = st.file_uploader("选择文件", # 文件上传组件的显示标签
                                  type=None, # 允许上传的文件类型：None 表示接受任何类型的文件
                                  accept_multiple_files=True) # 是否允许用户选择多个文件：True 表示允许

if uploaded_files: # 如果用户上传了文件（uploaded_files 不为空）
    st.write("已上传文件：") # 显示一个文本提示
    for uploaded_file in uploaded_files: # 遍历所有已上传的文件
        size_kb = uploaded_file.size / 1024 # 计算文件大小（字节）并转换为 KB
        st.write(f"- {uploaded_file.name} " # 显示文件名
                 f"(大小: {size_kb:.2f} KB)") # 显示文件大小，保留两位小数

    if st.button("生成ZIP压缩包"): # 显示一个按钮，用户点击后触发 ZIP 生成
        with st.spinner("正在生成ZIP文件..."): # 在生成过程中显示一个加载动画和文本
            zip_buffer = create_zip(uploaded_files) # 调用 create_zip 函数来生成 ZIP 文件数据
            
            if zip_buffer: # 如果 zip_buffer 不为 None（表示 ZIP 文件成功生成）
                # --- 优化 ZIP 文件名：使用第一个上传的文件名作为基础 ---
                first_file_name = os.path.splitext( # 获取第一个上传文件的名称，并分割文件名和扩展名
                    os.path.basename(uploaded_files[0].name))[0] # [0] 获取文件名部分 (不含扩展名)
                
                now = datetime.datetime.now() # 获取当前的日期和时间，精确到微秒
                # 格式：basename_YYYYMMDD_HHMMSS_milliseconds.zip
                timestamp = now.strftime("%Y%m%d_%H%M%S_%f")[:-3] # 格式化时间，%f 是微秒，[:-3] 截取前三位作为毫秒
                download_file_name = f"{first_file_name}_{timestamp}.zip" # 构建最终的下载文件名

                st.download_button(label="下载ZIP文件", # 下载按钮上显示的文本
                                   data=zip_buffer, # 要下载的数据源，即内存中的 ZIP 文件内容
                                   file_name=download_file_name, # 用户下载时保存的文件名
                                   mime="application/zip") # 下载文件的 MIME 类型，告诉浏览器这是个 ZIP 文件
                st.success("ZIP文件已成功生成。") # 显示成功消息
            else: # 如果 zip_buffer 为 None（表示 ZIP 文件生成失败）
                st.error("ZIP 文件生成失败。") # 显示错误消息
else: # 如果用户尚未上传任何文件
    st.info("请上传文件以开始。") # 显示提示信息，引导用户上传文件