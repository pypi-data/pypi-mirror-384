# -*- coding: utf-8 -*-
import streamlit as st
import os
import shutil
import platform
import sys
import pkg_resources # 用于获取已安装库的版本

# 定义主应用程序函数
def seven_zip_to_zip_converter_app():
    # --- 导入错误检测 ---
    try:
        import py7zr
    except ImportError:
        # 如果未找到 py7zr 库，显示警告信息并停止应用
        st.warning("错误：未找到 'py7zr' 库。请运行 'pip install py7zr' 安装它。")
        st.stop() # 停止 Streamlit 应用执行，因为缺少关键依赖
    try:
        import zipfile
    except ImportError:
        # 如果未找到 zipfile 库（通常是内置的），显示警告信息并停止应用
        st.warning("错误：未找到 'zipfile' 库。它通常是 Python 内置的，如果出现此错误，请检查你的 Python 环境。")
        st.stop() # 停止 Streamlit 应用执行

    # --- 配置 ---
    # 定义上传和输出目录的路径
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "converted_zips"

    # 创建目录（如果它们不存在）
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    except OSError as e:
        # 如果无法创建目录，显示警告信息并停止应用
        st.warning(f"无法创建必要的目录 '{UPLOAD_DIR}' 或 '{OUTPUT_DIR}'。请检查文件权限。错误：{e}")
        st.stop() # 无法创建目录则停止应用

    # 设置 Streamlit 页面配置
    st.set_page_config(
        page_title=".7z 到 .zip 转换器",
        page_icon="🗜️"
    )

    st.title("🗜️ .7z 到 .zip 转换器")
    st.write("上传你的 **.7z** 文件，我将帮你转换成 **.zip** 压缩包。")

    # --- 平台检测 ---
    current_os = platform.system()
    st.sidebar.info(f"当前操作系统：**{current_os}**")

    # --- 显示 Python 和库版本信息 ---
    st.sidebar.markdown("---") # 分隔线
    st.sidebar.subheader("环境信息")

    # Python 版本
    st.sidebar.write(f"**Python 版本:** {sys.version.split(' ')[0]}")

    # 库版本
    def get_package_version(package_name):
        """尝试获取指定包的版本。"""
        try:
            return pkg_resources.get_distribution(package_name).version
        except pkg_resources.DistributionNotFound:
            return "未安装或版本未知"
        except Exception as e:
            return f"获取失败: {e}"

    st.sidebar.write(f"**Streamlit 版本:** {get_package_version('streamlit')}")
    st.sidebar.write(f"**py7zr 版本:** {get_package_version('py7zr')}")
    st.sidebar.write(f"**zipfile 版本:** (内置模块，随 Python 版本)") # zipfile 是内置模块，版本与 Python 版本一致

    st.sidebar.markdown("---") # 分隔线

    if current_os == "Windows":
        st.sidebar.info("你正在 Windows 系统上运行。")
    elif current_os == "Linux":
        st.sidebar.info("你正在 Linux 系统上运行。")
    elif current_os == "Darwin": # macOS
        st.sidebar.info("你正在 macOS 系统上运行。")
    else:
        st.sidebar.info(f"你正在 {current_os} 系统上运行。")


    # 文件上传组件
    uploaded_file = st.file_uploader("选择一个 .7z 文件", type=["7z"])

    if uploaded_file is not None:
        original_filename = uploaded_file.name
        # 获取文件扩展名并转换为小写，方便比较
        file_extension = os.path.splitext(original_filename)[1]

        # 检查文件是否确实是 .7z 类型
        if file_extension.lower() != ".7z":
            st.warning("🚫 请上传一个有效的 **.7z** 文件。")
        else:
            # 构建上传文件的完整路径
            file_path_7z = os.path.join(UPLOAD_DIR, original_filename)
            try:
                # 以二进制写入模式保存上传的文件
                with open(file_path_7z, "wb") as f:
                    f.write(uploaded_file.getbuffer()) # 获取文件内容的字节缓冲区
                st.info(f"✅ 文件 '{original_filename}' 上传成功！")
            except IOError as e:
                st.warning(f"❌ 无法保存上传的文件。请检查服务器存储空间或权限。错误：{e}")
                st.stop() # 文件未成功保存，停止执行

            # 生成 .zip 输出文件的名称和路径
            zip_output_filename = os.path.splitext(original_filename)[0] + ".zip"
            zip_output_path = os.path.join(OUTPUT_DIR, zip_output_filename)

            # 为解压内容创建一个临时目录
            temp_extract_dir = os.path.join(UPLOAD_DIR, "temp_extracted_" + os.path.splitext(original_filename)[0])
            try:
                os.makedirs(temp_extract_dir, exist_ok=True)
            except OSError as e:
                st.warning(f"❌ 无法创建临时解压目录。请检查权限。错误：{e}")
                # 如果创建临时目录失败，尝试清理已上传的 .7z 文件
                if os.path.exists(file_path_7z):
                    os.remove(file_path_7z)
                st.stop() # 停止执行

            try:
                st.info("⚙️ 正在启动转换过程...")

                # --- 2. 解压 .7z 文件 ---
                try:
                    # 使用 py7zr 解压 .7z 存档
                    with py7zr.SevenZipFile(file_path_7z, mode='r') as archive:
                        archive.extractall(path=temp_extract_dir)
                    st.info("📦 .7z 文件内容已成功解压。")
                except py7zr.Bad7zFile:
                    st.warning("❌ 上传的文件不是有效的 .7z 压缩包或已损坏。")
                    st.stop()
                except py7zr.NoSuchFileOrDirectory:
                    st.warning("❌ 无法找到 .7z 文件，请重试。")
                    st.stop()
                except Exception as e:
                    st.warning(f"❌ 解压 .7z 文件时发生未知错误：{e}")
                    st.stop()

                # --- 3. 创建 .zip 文件 ---
                try:
                    # 使用 zipfile 模块创建 .zip 压缩包
                    with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        # 遍历临时解压目录中的所有文件和子目录
                        for root, _, files in os.walk(temp_extract_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # arcname 用于在 zip 文件中保持正确的相对路径结构
                                arcname = os.path.relpath(file_path, temp_extract_dir)
                                zipf.write(file_path, arcname)
                    st.success("🎉 转换为 .zip 文件完成！")
                except Exception as e:
                    st.warning(f"❌ 创建 .zip 文件时发生错误：{e}")
                    st.stop()

                # --- 4. 提供下载链接 ---
                if os.path.exists(zip_output_path):
                    try:
                        with open(zip_output_path, "rb") as f:
                            st.download_button(
                                label="⬇️ 下载你的 .zip 文件",
                                data=f.read(),
                                file_name=zip_output_filename,
                                mime="application/zip"
                            )
                    except IOError as e:
                        st.warning(f"❌ 无法读取生成的 .zip 文件进行下载。错误：{e}")
                else:
                    st.warning("❌ .zip 文件未成功生成，无法提供下载。")

            except Exception as e:
                st.warning(f"❌ 转换过程中发生意外错误：{e}")
            finally:
                # --- 清理：移除临时文件和目录 ---
                st.info("🧹 正在清理临时文件...")
                if os.path.exists(file_path_7z):
                    try:
                        os.remove(file_path_7z)
                        st.sidebar.info("✅ 已删除上传的 .7z 文件。")
                    except OSError as e:
                        st.sidebar.warning(f"⚠️ 无法删除上传的 .7z 文件：{e}")
                if os.path.exists(temp_extract_dir):
                    try:
                        shutil.rmtree(temp_extract_dir)
                        st.sidebar.info("✅ 已删除临时解压目录。")
                    except OSError as e:
                        st.sidebar.warning(f"⚠️ 无法删除临时解压目录：{e}")
                # 注意：生成的 .zip 文件默认在会话结束或清除前不会自动删除。
                # 如需自动删除，需更复杂的逻辑，例如结合 Streamlit 的 session state 或定期清理任务。

# 当脚本直接运行时，调用主应用程序函数
if __name__ == "__main__":
    seven_zip_to_zip_converter_app()
