import streamlit as st
import tempfile
import os
from PIL import Image  # 用于处理图片
import pandas as pd  # 用于处理 Excel

# --- Streamlit 应用界面 ---
st.title("文件上传与处理应用")
st.write("请上传图片、音乐、视频或 Excel 文件，我会尝试处理并显示其内容。")

aaa = st.file_uploader("请选择一个文件进行上传", type=["jpg", "jpeg", "png", "gif",  # 图片
                                                 "mp3", "wav", "ogg",            # 音乐
                                                 "mp4", "mov", "avi",            # 视频
                                                 "xls", "xlsx"])                 # Excel

if aaa:
    # 获取文件类型（MIME type）
    file_type = aaa.type
    st.info(f"检测到的文件类型: **{file_type}**")

    # --- 将上传文件保存到临时文件 ---
    # Streamlit 的 file_uploader 返回的文件对象通常是内存中的，
    # 而许多处理文件的库需要实际的文件路径。
    # tempfile 模块允许安全地创建临时文件。
    
    # 获取原始文件的扩展名，用于临时文件
    file_extension = os.path.splitext(aaa.name)[1]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(aaa.read())
        temp_file_path = temp_file.name

    st.success(f"文件已临时保存到: `{temp_file_path}`")

    # --- 根据文件类型选择处理方法 ---
    # 图片文件处理
    if file_type.startswith("image/"):
        st.subheader("🖼️ 图片文件处理")
        try:
            image = Image.open(temp_file_path)
            st.image(image, caption=f"上传的图片: {aaa.name}", use_column_width=True)
            st.write(f"图片尺寸: **{image.size[0]} x {image.size[1]} 像素**")
            st.write(f"图片格式: **{image.format}**")
            # 可以在这里添加更多图片处理逻辑，例如：
            # image.thumbnail((128, 128)) # 缩小图片
            # st.image(image, caption="缩小后的图片", width=150)
        except Exception as e:
            st.error(f"处理图片时发生错误: {e}")

    # 音乐文件处理
    elif file_type.startswith("audio/"):
        st.subheader("🎵 音乐文件处理")
        st.audio(temp_file_path, format=file_type)
        st.info("Streamlit 内置播放器将尝试播放该音频。对于更复杂的音频处理，需要专门的 Python 库。")

    # 视频文件处理
    elif file_type.startswith("video/"):
        st.subheader("🎬 视频文件处理")
        st.video(temp_file_path, format=file_type)
        st.info("Streamlit 内置播放器将尝试播放该视频。对于视频分析或编辑，需要像 OpenCV 这样的库。")

    # Excel 文件处理
    elif file_type == "application/vnd.ms-excel" or \
         file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        st.subheader("📊 Excel 文件处理")
        try:
            df = pd.read_excel(temp_file_path)
            st.success("Excel 文件读取成功！")
            st.write("文件内容预览 (前5行):")
            st.dataframe(df.head()) # 显示前5行
            st.write(f"Excel 文件包含 **{df.shape[0]} 行** 和 **{df.shape[1]} 列**。")
            # 可以在这里添加更多 Excel 数据处理逻辑，例如：
            # st.write("数据统计摘要:")
            # st.write(df.describe())
        except Exception as e:
            st.error(f"处理 Excel 文件时发生错误: {e}")

    # 其他未支持的文件类型
    else:
        st.warning(f"🤔 抱歉，当前不支持处理类型为 `{file_type}` 的文件。")

    # --- 清理临时文件 ---
    # 确保文件处理完成后删除临时文件，避免占用磁盘空间。
    os.unlink(temp_file_path)
    st.info("临时文件已删除。")