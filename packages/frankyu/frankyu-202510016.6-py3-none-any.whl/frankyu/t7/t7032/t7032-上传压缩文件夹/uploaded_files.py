import streamlit as st # 用于构建交互式Web应用
import os # 提供与操作系统交互的功能，如路径操作
from io import BytesIO # 用于在内存中处理二进制数据流
import datetime # 用于处理日期和时间
import platform # 用于获取操作系统信息
import sys # 用于获取Python版本和退出应用

# --- 核心模块的直接导入 ---
# 将 zipfile 模块直接放在顶部导入，确保它在所有函数定义时都可用
try:
    import zipfile # 核心模块，用于创建和读取 ZIP 压缩文件
except ImportError:
    # 如果 zipfile 缺失，应用无法提供核心功能，立即停止
    st.error("严重错误：缺少核心模块 'zipfile'。此应用无法运行。")
    st.error("请尝试运行：`pip install zipfile`")
    st.stop() # 停止 Streamlit 应用的执行

# --- 尝试导入可选模块 ---
# is_pillow_available 用于标记 Pillow 是否可用，默认为 False
is_pillow_available = False
try:
    from PIL import Image # 尝试导入 Pillow 库的 Image 模块
    is_pillow_available = True # 如果导入成功，则设置为 True
except ImportError:
    st.warning("警告：未安装 'Pillow' 库。图片预览功能将不可用。")
    st.info("如需图片预览，请运行：`pip install Pillow`")
    # 不停止应用，只跳过相关功能

# --- 全局配置常量 ---
DEFAULT_ZIP_MIME_TYPE = "application/zip" # ZIP文件的默认MIME类型
DEFAULT_PAGE_TITLE = "增强版文件夹压缩工具" # 默认页面标题
DEFAULT_PAGE_LAYOUT = "centered" # 默认页面布局
DEFAULT_FILE_UPLOADER_LABEL = "请选择要压缩的文件夹内的所有文件" # 文件上传器默认标签
DEFAULT_FOLDER_NAME_INPUT_LABEL = "请输入要压缩的文件夹名称（将作为ZIP文件名的一部分）" # 新增：文件夹名称输入框标签
DEFAULT_GENERATE_BUTTON_LABEL = "生成ZIP压缩包" # 生成ZIP按钮默认标签
DEFAULT_DOWNLOAD_BUTTON_LABEL = "点击下载ZIP文件" # 下载按钮默认标签
DEFAULT_SPINNER_TEXT = "正在努力生成ZIP文件..." # 生成ZIP时的默认加载文本
DEFAULT_SUCCESS_MESSAGE = "ZIP文件已成功生成并可下载！" # 成功生成ZIP后的默认消息
DEFAULT_ERROR_MESSAGE_ZIP_FAILED = "抱歉，ZIP文件生成失败。请检查文件或稍后重试。" # ZIP生成失败的默认错误消息
DEFAULT_INFO_MESSAGE_NO_FILES = "请上传文件以开始压缩和下载。" # 没有文件时的默认提示信息
DEFAULT_WARNING_MESSAGE_NO_FILES_TO_ZIP = "没有检测到任何文件可供打包。请上传文件。" # 没有文件可打包时的默认警告
DEFAULT_OS_UNSUPPORTED_MESSAGE = "抱歉，此应用在您的操作系统上可能无法完全兼容。当前操作系统：" # 操作系统不支持时的默认消息


# --- 核心模块检查函数（现在更侧重于运行时检查） ---
def check_zipfile_availability(error_message: str = "错误：zipfile 模块在运行时出现问题，请检查您的Python环境。") -> None:
    """
    在运行时检查 zipfile 模块是否可用，以防出现更深层次的问题。

    :param error_message: 当 zipfile 模块不可用时显示给用户的错误消息。
    :type error_message: str
    """
    __doc__ = "在运行时检查 zipfile 模块是否可用。"
    # 由于 zipfile 已在顶部导入，这里主要检查其功能是否正常或是否被意外覆盖
    if 'zipfile' not in sys.modules: # 检查模块是否在已加载模块列表中
        st.error(error_message)
        st.stop()
    # 可以在这里添加更复杂的检查，例如尝试创建 ZipFile 对象来验证功能


# --- 操作系统检测函数 ---
def detect_os(unsupported_message: str = DEFAULT_OS_UNSUPPORTED_MESSAGE # 操作系统不受支持时的消息前缀
             ) -> str:
    """
    检测运行 Streamlit 应用的操作系统，并可在侧边栏显示信息。

    :param unsupported_message: 当检测到可能不受支持的操作系统时，显示给用户的消息前缀。
                                默认为 DEFAULT_OS_UNSUPPORTED_MESSAGE。
    :type unsupported_message: str
    :return: 当前操作系统的名称（例如 'Windows', 'Linux', 'Darwin' (macOS)）。
    :rtype: str
    """
    __doc__ = "检测运行 Streamlit 应用的操作系统。"
    current_os = platform.system() # 获取操作系统名称
    
    st.sidebar.info(f"当前操作系统：**{current_os}**") # 在侧边栏显示操作系统信息
    st.sidebar.info(f"Python版本：**{sys.version.split(' ')[0]}**") # 在侧边栏显示Python版本
    
    return current_os

# --- 文件压缩核心函数 ---
def create_zip_archive(files: list, # 包含上传文件对象的列表
                        folder_name: str = "", # 新增：用于在ZIP中创建文件夹结构的名称
                        compression_method: int = zipfile.ZIP_DEFLATED, # 压缩方法，默认为 DEFLATE
                        allow_zip64: bool = False, # 是否启用 ZIP64 扩展（支持大文件），默认为 False
                        warning_no_files: str = DEFAULT_WARNING_MESSAGE_NO_FILES_TO_ZIP, # 没有文件时显示的警告消息
                        error_file_write: str = "写入文件到ZIP失败：", # 单个文件写入失败时的错误前缀
                        error_zip_creation: str = "创建ZIP压缩包时发生意外错误：" # ZIP创建失败时的错误前缀
                      ) -> BytesIO | None:
    """
    将给定的文件列表打包成一个ZIP格式的内存缓冲区。
    可以指定一个文件夹名称，将所有文件放入该文件夹内。
    提供详细的错误处理，包括空文件列表、单个文件写入失败和整体ZIP创建错误。

    :param files: 包含 Streamlit UploadedFile 对象的列表。
    :type files: list
    :param folder_name: 在ZIP文件中创建的虚拟文件夹的名称。如果为空，文件将直接在根目录。
    :type folder_name: str
    :param compression_method: ZIP压缩方法，例如 zipfile.ZIP_DEFLATED (默认) 或 zipfile.ZIP_STORED。
    :type compression_method: int
    :param allow_zip64: 如果为 True，则允许创建 Zip64 格式的归档，支持大于 4GB 的文件，默认为 False。
    :type allow_zip64: bool
    :param warning_no_files: 当文件列表为空时显示的警告消息。
    :type warning_no_files: str
    :param error_file_write: 当单个文件写入 ZIP 失败时，错误消息的前缀。
    :type error_file_write: str
    :param error_zip_creation: 当 ZIP 归档创建过程中发生意外错误时，错误消息的前缀。
    :type error_zip_creation: str
    :return: 包含 ZIP 文件内容的 BytesIO 对象，如果发生错误则返回 None。
    :rtype: BytesIO | None
    """
    __doc__ = "将给定的文件列表打包成一个ZIP格式的内存缓冲区。"
    if not files:
        st.warning(warning_no_files)
        return None

    zip_buffer = BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer,
                             "a", # 'a' for append, 'w' for write (overwrite)
                             compression_method,
                             allow_zip64) as zip_file:
            for uploaded_file in files:
                try:
                    # 如果提供了文件夹名称，则在ZIP内创建该文件夹结构
                    arcname = os.path.join(folder_name, os.path.basename(uploaded_file.name)) if folder_name else os.path.basename(uploaded_file.name)
                    file_content = uploaded_file.getvalue()
                    zip_file.writestr(arcname, file_content)
                except Exception as e:
                    st.error(f"{error_file_write}'{uploaded_file.name}': {e}")
                    return None
        zip_buffer.seek(0)
        return zip_buffer
    except Exception as e:
        st.error(f"{error_zip_creation}{e}")
        return None

# --- 文件名生成函数 ---
def generate_zip_filename(base_name: str, # 新增：作为ZIP文件名的基础名称
                          prefix: str = "compressed", # 文件名的前缀
                          suffix: str = "", # 文件名的后缀
                          include_timestamp: bool = True, # 是否包含时间戳
                          include_milliseconds: bool = True, # 时间戳是否包含毫秒
                          timestamp_format: str = "%Y%m%d_%H%M%S", # 日期时间格式字符串
                          milliseconds_delimiter: str = "_", # 毫秒与秒之间的分隔符
                          zip_extension: str = ".zip" # ZIP文件的扩展名
                         ) -> str:
    """
    根据提供的基础名称和配置生成一个带有时间戳的ZIP文件名。
    文件名基础通常是用户输入的“文件夹名称”。

    :param base_name: ZIP文件名的基础部分，通常是用户输入的文件夹名称。
    :type base_name: str
    :param prefix: ZIP文件名的前缀字符串，默认为 "compressed"。最终是 prefix_base_name_timestamp.zip。
    :type prefix: str
    :param suffix: ZIP文件名的后缀字符串，默认为空。
    :type suffix: str
    :param include_timestamp: 是否在文件名中包含当前时间戳，默认为 True。
    :type include_timestamp: bool
    :param include_milliseconds: 如果 include_timestamp 为 True，是否在时间戳中包含毫秒，默认为 True。
    :type include_milliseconds: bool
    :param timestamp_format: Python datetime strftime 格式字符串，用于生成日期时间部分。
                              默认为 "%Y%m%d_%H%M%S"。
    :type timestamp_format: str
    :param milliseconds_delimiter: 毫秒部分与秒部分之间的分隔符，默认为 "_"。
    :type milliseconds_delimiter: str
    :param zip_extension: ZIP文件的扩展名，默认为 ".zip"。
    :type zip_extension: str
    :return: 生成的ZIP文件名，例如 "compressed_MyFolder_20231027_143000_123.zip"。
    :rtype: str
    """
    __doc__ = "根据提供的基础名称和配置生成一个带有时间戳的ZIP文件名。"
    
    parts = []
    if prefix:
        parts.append(prefix)
    
    if base_name:
        parts.append(base_name)

    if include_timestamp:
        now = datetime.datetime.now()
        current_timestamp = now.strftime(timestamp_format)
        if include_milliseconds:
            milliseconds = str(now.microsecond)[:3].ljust(3, '0')  # 取前三位，不足补0
            current_timestamp += f"{milliseconds_delimiter}{milliseconds}"
        parts.append(current_timestamp)
    
    if suffix:
        parts.append(suffix)

    file_name_without_ext = "_".join(parts).strip("_")  # 移除可能的多余下划线

    if not file_name_without_ext:
        file_name_without_ext = "compressed_folder" # 如果没有提供任何名称，使用默认值

    return f"{file_name_without_ext}{zip_extension}"


# --- 辅助函数：尝试显示图片预览 ---
def display_image_preview(uploaded_file, # 上传的文件对象
                          max_width: int = 200, # 图片预览的最大宽度
                          caption_prefix: str = "预览：" # 预览图片的标题前缀
                         ) -> None:
    """
    如果 Pillow 库可用，尝试显示上传图片的预览。

    :param uploaded_file: Streamlit UploadedFile 对象。
    :type uploaded_file: object
    :param max_width: 图片在 Streamlit 界面显示的最大宽度（像素），默认为 200。
    :type max_width: int
    :param caption_prefix: 预览图片标题的前缀字符串，默认为 "预览："。
    :type caption_prefix: str
    """
    __doc__ = "尝试显示上传图片的预览。"
    global is_pillow_available # 声明使用全局变量
    
    if not is_pillow_available: # 如果 Pillow 不可用，直接返回
        return

    # 检查文件类型是否为图片 (简单检查，可以更完善)
    if uploaded_file.type and uploaded_file.type.startswith('image/'):
        try:
            image = Image.open(uploaded_file) # 使用 Pillow 打开图片
            st.image(image, # 显示图片
                     caption=f"{caption_prefix}{uploaded_file.name}", # 图片标题
                     width=max_width) # 设置图片宽度
        except Exception as e:
            st.warning(f"无法预览图片 '{uploaded_file.name}'：{e}") # 显示无法预览的警告


# --- Streamlit 应用主函数 ---
def main_app(page_title: str = DEFAULT_PAGE_TITLE, # Streamlit页面的标题
             page_layout: str = DEFAULT_PAGE_LAYOUT, # Streamlit页面的布局
             uploader_label: str = DEFAULT_FILE_UPLOADER_LABEL, # 文件上传器的显示标签
             folder_name_label: str = DEFAULT_FOLDER_NAME_INPUT_LABEL, # 文件夹名称输入框标签
             uploader_types: list | None = None, # 允许上传的文件类型列表，None表示所有类型
             uploader_multiple: bool = True, # 是否允许上传多个文件
             generate_btn_label: str = DEFAULT_GENERATE_BUTTON_LABEL, # "生成ZIP"按钮的标签
             download_btn_label: str = DEFAULT_DOWNLOAD_BUTTON_LABEL, # "下载ZIP"按钮的标签
             spinner_text: str = DEFAULT_SPINNER_TEXT, # 生成ZIP时的加载文本
             success_msg: str = DEFAULT_SUCCESS_MESSAGE, # 成功消息
             error_msg_zip_fail: str = DEFAULT_ERROR_MESSAGE_ZIP_FAILED, # ZIP生成失败的错误消息
             info_msg_no_files: str = DEFAULT_INFO_MESSAGE_NO_FILES # 没有文件时的信息提示
            ) -> None:
    """
    构建并运行 Streamlit 文件压缩下载 Web 应用的主逻辑。

    :param page_title: Streamlit 页面在浏览器标签页上的标题，默认为 DEFAULT_PAGE_TITLE。
    :type page_title: str
    :param page_layout: Streamlit 页面的布局模式，可以是 "centered" 或 "wide"，默认为 DEFAULT_PAGE_LAYOUT。
    :type page_layout: str
    :param uploader_label: 文件上传组件上显示的文本标签，默认为 DEFAULT_FILE_UPLOADER_LABEL。
    :type uploader_label: str
    :param folder_name_label: 用于输入目标文件夹名称的文本框标签。
    :type folder_name_label: str
    :param uploader_types: 允许用户上传的文件扩展名列表（例如 ['png', 'jpg']），None 表示允许所有类型。
    :type uploader_types: list | None
    :param uploader_multiple: 如果为 True，则允许用户一次上传多个文件，默认为 True。
    :type uploader_multiple: bool
    :param generate_btn_label: “生成ZIP压缩包”按钮上显示的文本，默认为 DEFAULT_GENERATE_BUTTON_LABEL。
    :type generate_btn_label: str
    :param download_btn_label: “下载ZIP文件”按钮上显示的文本，默认为 DEFAULT_DOWNLOAD_BUTTON_LABEL。
    :type download_btn_label: str
    :param spinner_text: 在ZIP文件生成过程中显示的加载文本，默认为 DEFAULT_SPINNER_TEXT。
    :type spinner_text: str
    :param success_msg: ZIP文件成功生成后显示给用户的成功消息，默认为 DEFAULT_SUCCESS_MESSAGE。
    :type success_msg: str
    :param error_msg_zip_fail: 当ZIP文件生成失败时显示给用户的错误消息，默认为 DEFAULT_ERROR_MESSAGE_ZIP_FAILED。
    :type error_msg_zip_fail: str
    :param info_msg_no_files: 当用户尚未上传任何文件时显示的信息提示，默认为 DEFAULT_INFO_MESSAGE_NO_FILES。
    :type info_msg_no_files: str
    """
    __doc__ = "构建并运行 Streamlit 文件压缩下载 Web 应用的主逻辑。"
    st.set_page_config(page_title=page_title, layout=page_layout)

    st.title(page_title)
    st.write("欢迎使用文件夹压缩工具。")
    st.write("请选择您要压缩的文件夹内的所有文件，并可以为此“文件夹”命名，我们将它们打包成一个ZIP文件。")

    # 新增：让用户输入一个“文件夹名称”，这个名称将用于ZIP内部的目录结构以及最终ZIP文件的命名
    folder_name = st.text_input(folder_name_label, value="MyCompressedFolder")


    uploaded_files = st.file_uploader(uploader_label,
                                      type=uploader_types,
                                      accept_multiple_files=uploader_multiple)

    if uploaded_files:
        st.write("您已选择以下文件：")
        for uploaded_file in uploaded_files:
            size_kb = uploaded_file.size / 1024
            st.write(f"- **{uploaded_file.name}** ({size_kb:.2f} KB)")
            # 尝试显示图片预览 (如果 Pillow 可用)
            display_image_preview(uploaded_file)  # 注意：这里预览的是原始文件，不是压缩后的

        if st.button(generate_btn_label):
            with st.spinner(spinner_text):
                # 调用新的 create_zip_archive，传入 folder_name
                zip_buffer = create_zip_archive(uploaded_files, folder_name=folder_name)
                
                if zip_buffer:
                    # 使用新的 generate_zip_filename，传入 folder_name 作为 base_name
                    download_file_name = generate_zip_filename(folder_name,
                                                               prefix="compressed", 
                                                               include_milliseconds=True)
                    
                    st.download_button(label=download_btn_label,
                                       data=zip_buffer,
                                       file_name=download_file_name,
                                       mime=DEFAULT_ZIP_MIME_TYPE)
                    st.success(success_msg)
                else:
                    st.error(error_msg_zip_fail)
    else:
        st.info(info_msg_no_files)

# --- 应用入口点 ---
if __name__ == "__main__":
    # 在运行主应用前，确保 zipfile 模块可用（因为它已在顶部导入）
    check_zipfile_availability()  
    # 检测操作系统并显示信息
    detect_os()  
    main_app() # 运行 Streamlit 应用的主函数