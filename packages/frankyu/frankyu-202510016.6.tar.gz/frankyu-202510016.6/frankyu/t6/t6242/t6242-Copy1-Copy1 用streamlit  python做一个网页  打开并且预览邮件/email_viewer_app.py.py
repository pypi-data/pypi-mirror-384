import streamlit as st
import os
import tempfile
from email import policy
from email.parser import BytesParser
import extract_msg  # 用于处理.msg文件
from PIL import Image
import io
import base64
import re
from datetime import datetime
from bs4 import BeautifulSoup # 导入BeautifulSoup，用于HTML解析和清理
import bleach # 导入bleach，用于更严格的HTML净化

# --- Streamlit 页面配置 ---
st.set_page_config(
    page_title="邮件预览器",
    page_icon=":email:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 自定义CSS样式 ---
st.markdown("""
<style>
    /* 页面头部样式 */
    .header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .header h1 {
        margin: 0;
        font-size: 2.5rem;
    }

    /* 文件上传区域样式 */
    .file-uploader {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .file-uploader h3 {
        color: #2c3e50;
        margin-bottom: 1rem;
    }

    /* 预览区块通用样式 */
    .preview-section {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .preview-title {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        font-size: 1.8rem;
    }

    /* 邮件头信息样式 */
    .email-header {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 5px solid #3498db;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
    }
    .email-header strong {
        color: #0056b3;
    }

    /* 附件卡片样式 */
    .attachment-card {
        background-color: #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border: 1px solid #dee2e6;
        transition: transform 0.2s;
    }
    .attachment-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Streamlit 按钮样式 */
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
        font-weight: bold;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        color: white;
    }

    /* 邮件正文容器样式 */
    .email-body-container {
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        min-height: 200px;
        max-height: 600px;
        overflow-y: auto;
        background-color: #fff;
        font-family: Arial, sans-serif;
        color: #444;
        line-height: 1.5;
    }
    .email-body-container::-webkit-scrollbar {
        width: 8px;
    }
    .email-body-container::-webkit-scrollbar-thumb {
        background-color: #ccc;
        border-radius: 4px;
    }
    .email-body-container::-webkit-scrollbar-track {
        background-color: #f0f0f0;
    }

    /* 图片预览容器和项目样式 */
    .image-preview-container {
        display: flex;
        flex-wrap: wrap;
        gap: 25px; /* 增加间距 */
        margin-top: 15px;
        padding: 10px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: #fdfdfd;
        overflow-x: auto; /* 允许横向滚动 */
        max-height: 500px; /* 限制高度 */
        align-items: flex-start; /* 顶部对齐 */
    }
    .image-preview-item {
        border: 1px solid #ddd;
        padding: 12px; /* 增加内边距 */
        border-radius: 10px; /* 增加圆角 */
        text-align: center;
        max-width: 450px; /* 放大卡片，原150px的3倍 */
        min-width: 300px; /* 最小宽度 */
        box-shadow: 0 2px 6px rgba(0,0,0,0.15); /* 增强阴影 */
        background-color: #fff;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s;
    }
    .image-preview-item:hover {
        transform: scale(1.03); /* 放大效果 */
        box-shadow: 0 3px 8px rgba(0,0,0,0.2); /* 更强阴影 */
    }
    .image-preview-item img {
        max-width: 100%;
        height: auto;
        max-height: 360px; /* 限制图片高度，原120px的3倍 */
        object-fit: contain; /* 保持图片比例 */
        border-radius: 8px; /* 圆角 */
        margin-bottom: 12px; /* 增加下边距 */
        border: 1px solid #f0f0f0;
    }
    .image-preview-item p {
        font-size: 0.95em; /* 稍微放大字体 */
        word-break: break-all;
        margin: 0;
        color: #555;
        max-height: 4em; /* 限制文件名显示行数 */
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .image-preview-item .image-download-button {
        margin-top: 15px; /* 增加上边距 */
        display: inline-block;
    }

    /* Streamlit 警告/信息/错误消息的额外样式 */
    .stAlert {
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 初始化邮件数据变量 ---
email_data = {
    "subject": "未选择邮件",
    "from": "",
    "to": "",
    "date": "",
    "body": "",  # 纯文本正文
    "html": "",  # HTML正文
    "attachments": [],  # 普通附件列表
    "embedded_images_for_display": [] # 专门用于显示内联图片和附件中的图片
}

# --- 辅助函数：将Content-ID替换为Base64 Data URI ---
def replace_cid_with_base64(html_content, embedded_images):
    """
    使用BeautifulSoup将HTML内容中的CID引用替换为Base64 Data URI。
    """
    if not html_content:
        return ""
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for img_info in embedded_images:
            cid = img_info["cid"]
            data_uri = f'data:image/{img_info["type"].lower() if img_info["type"] else "png"};base64,{img_info["data"]}'
            
            # 查找所有带有对应CID的img标签
            for img_tag in soup.find_all('img', src=re.compile(rf'cid:{re.escape(cid)}', re.IGNORECASE)):
                img_tag['src'] = data_uri
        return str(soup)
    except Exception as e:
        st.warning(f"替换CID图片时发生错误: {e}. 尝试显示原始HTML。")
        return html_content

# --- 辅助函数：HTML内容清理 (更严格的版本) ---
def clean_html(html_content):
    """
    使用BeautifulSoup和Bleach清理HTML内容，移除script/style标签，
    并限制允许的标签和属性，以防止无效标签名错误。
    """
    if not html_content:
        return ""
    try:
        # 使用BeautifulSoup进行初步解析和修复
        soup = BeautifulSoup(html_content, 'lxml') # 'lxml' is generally more robust
        # 移除 script 和 style 标签
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
        
        cleaned_soup_str = str(soup)

        # 定义允许的HTML标签和属性。这个列表可以根据需求调整。
        # 这是一个相对安全的默认列表，避免了大多数潜在问题。
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'p',
            'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'br', 'span', 'div',
            'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'img', 's', 'u', 'font',
            'hr', 'small', 'big', 'cite', 'sub', 'sup', 'del', 'ins', 'dl', 'dt', 'dd'
        ]
        allowed_attrs = {
            '*': ['id', 'class', 'style', 'title'], # 允许所有标签有这些通用属性
            'a': ['href', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height', 'data-src'], # 允许img标签的这些属性
            'td': ['colspan', 'rowspan'],
            'th': ['colspan', 'rowspan'],
            'font': ['color', 'face', 'size'] # 电子邮件中常见
        }
        allowed_styles = [
            'color', 'background-color', 'font-size', 'font-family', 'text-align',
            'margin', 'padding', 'border', 'width', 'height', 'line-height',
            'float', 'clear', 'display', 'vertical-align', 'text-decoration',
            'font-weight', 'font-style', 'margin-left', 'margin-right', 'margin-top', 'margin-bottom',
            'padding-left', 'padding-right', 'padding-top', 'padding-bottom',
            'border-collapse', 'border-spacing', 'border-top', 'border-right', 'border-bottom', 'border-left',
            'background', 'background-image', 'background-position', 'background-repeat', 'background-size'
        ]

        # 使用 bleach 进行更严格的清理
        cleaned_html = bleach.clean(
            cleaned_soup_str,
            tags=allowed_tags,
            attributes=allowed_attrs,
            styles=allowed_styles,
            strip=True, # 移除不允许的标签
            strip_comments=True # 移除HTML注释
        )
        return cleaned_html
    except Exception as e:
        st.error(f"HTML 清理失败: {e}. 这可能是因为HTML结构极其不规范。将尝试显示纯文本。")
        # 如果清理失败，返回空字符串或提示，以便显示纯文本
        return "" 

# --- 邮件解析函数：处理 .eml 文件 ---
def parse_eml(file_content):
    """
    解析.eml文件内容，提取邮件头、正文、附件和内联图片。
    """
    email_data_local = {
        "subject": "无主题", "from": "未知发件人", "to": "未知收件人",
        "date": "未知日期", "body": "", "html": "",
        "attachments": [], "embedded_images_for_display": []
    }
    
    try:
        msg = BytesParser(policy=policy.default).parsebytes(file_content)
        
        email_data_local["subject"] = msg.get("Subject", "无主题")
        email_data_local["from"] = msg.get("From", "未知发件人")
        email_data_local["to"] = msg.get("To", "未知收件人")
        email_data_local["date"] = msg.get("Date", "未知日期")

        embedded_images_raw = [] # 用于CID替换的原始内联图片数据

        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition", "")
            filename = part.get_filename()

            # 提取纯文本正文
            if part.get_content_maintype() == 'text' and content_type == 'text/plain' and 'attachment' not in content_disposition:
                charset = part.get_content_charset()
                try:
                    email_data_local["body"] = part.get_payload(decode=True).decode(charset if charset else 'utf-8', errors='ignore')
                except Exception as e:
                    st.warning(f"解码纯文本正文失败 ({charset}): {e}. 尝试 latin-1 解码。")
                    email_data_local["body"] = part.get_payload(decode=True).decode('latin-1', errors='ignore')
            
            # 提取HTML正文
            elif part.get_content_maintype() == 'text' and content_type == 'text/html' and 'attachment' not in content_disposition:
                charset = part.get_content_charset()
                try:
                    email_data_local["html"] = part.get_payload(decode=True).decode(charset if charset else 'utf-8', errors='ignore')
                except Exception as e:
                    st.warning(f"解码HTML正文失败 ({charset}): {e}. 尝试 latin-1 解码。")
                    email_data_local["html"] = part.get_payload(decode=True).decode('latin-1', errors='ignore')

            # 处理附件（非内联图片）
            elif "attachment" in content_disposition or (filename and not part.get('Content-ID')):
                if filename:
                    try:
                        file_data = part.get_payload(decode=True)
                        mime_type = part.get_content_type()
                        email_data_local["attachments"].append({"filename": filename, "data": file_data, "mime_type": mime_type})
                        
                        # 检查附件是否为图片，如果是，也添加到图片预览列表
                        if mime_type.startswith('image/'):
                            try:
                                img = Image.open(io.BytesIO(file_data))
                                buffered = io.BytesIO()
                                img_format = img.format if img.format in ["PNG", "JPEG", "GIF", "BMP"] else "PNG"
                                img.save(buffered, format=img_format)
                                img_str = base64.b64encode(buffered.getvalue()).decode()
                                email_data_local["embedded_images_for_display"].append({
                                    "filename": filename,
                                    "data_uri": f"data:image/{img_format.lower()};base64,{img_str}",
                                    "is_attachment": True # 标记为附件图片
                                })
                            except Exception as img_e:
                                st.warning(f"无法预览附件图片 {filename}: {img_e}")
                    except Exception as e:
                        st.warning(f"无法解析附件 {filename}: {e}")
            
            # 处理内联图片 (Content-ID)
            elif part.get_content_maintype() == 'image' and part.get('Content-ID'):
                cid = part.get('Content-ID').strip('<>')
                if not cid: # 忽略没有有效CID的内联图片
                    continue
                try:
                    img_data = part.get_payload(decode=True)
                    img = Image.open(io.BytesIO(img_data))
                    buffered = io.BytesIO()
                    img_format = img.format if img.format in ["PNG", "JPEG", "GIF", "BMP"] else "PNG"
                    img.save(buffered, format=img_format)
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    embedded_images_raw.append({"cid": cid, "data": img_str, "type": img_format})
                    email_data_local["embedded_images_for_display"].append({
                        "filename": filename if filename else f"inline_image_{cid}.{img_format.lower()}",
                        "data_uri": f"data:image/{img_format.lower()};base64,{img_str}",
                        "is_attachment": False # 标记为内联图片
                    })
                except Exception as e:
                    st.warning(f"无法处理内联图片（EML CID: {cid} - {filename if filename else '未知文件名'}）: {e}")

        # 在所有部分解析完毕后，替换HTML正文中的CID引用
        if email_data_local["html"] and embedded_images_raw:
            email_data_local["html"] = replace_cid_with_base64(email_data_local["html"], embedded_images_raw)

        # 如果只有HTML正文，尝试将其转换为纯文本作为备用
        if not email_data_local["body"] and email_data_local["html"]:
            soup = BeautifulSoup(email_data_local["html"], 'html.parser')
            email_data_local["body"] = soup.get_text(separator='\n')

    except Exception as e:
        st.error(f"解析 .eml 文件时发生错误: {e}")
        email_data_local["subject"] = "EML 文件解析失败"
        email_data_local["body"] = f"文件解析时发生错误: {e}"
        # 清空其他数据以避免显示不完整或错误信息
        email_data_local["html"] = ""
        email_data_local["attachments"] = []
        email_data_local["embedded_images_for_display"] = []

    return email_data_local

# --- 邮件解析函数：处理 .msg 文件 ---
def parse_msg(file_content):
    """
    解析.msg文件内容，提取邮件头、正文、附件和内联图片。
    """
    email_data_local = {
        "subject": "无主题", "from": "未知发件人", "to": "未知收件人",
        "date": "未知日期", "body": "", "html": "",
        "attachments": [], "embedded_images_for_display": []
    }
    
    tmp_file_path = None
    try:
        # 将上传的文件内容写入临时文件，供 extract_msg 处理
        with tempfile.NamedTemporaryFile(delete=False, suffix=".msg") as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        msg = extract_msg.Message(tmp_file_path)
        
        email_data_local["subject"] = msg.subject if msg.subject else "无主题"
        email_data_local["from"] = msg.sender if msg.sender else "未知发件人"
        email_data_local["to"] = msg.to if msg.to else "未知收件人"
        
        email_data_local["date"] = msg.date if msg.date else "未知日期"
        try:
            # 尝试解析并重新格式化日期以保持一致性
            # extract_msg 的日期格式可能不同，这里尝试常见格式
            # 例如 "Mon, 24 Jun 2024 15:30:00 +0800"
            date_obj = datetime.strptime(email_data_local["date"], "%a, %d %b %Y %H:%M:%S %z")
            email_data_local["date"] = date_obj.strftime("%Y-%m-%d %H:%M:%S %Z")
        except ValueError:
            pass # 如果解析失败，保留原始日期字符串

        email_data_local["body"] = msg.body if msg.body else ""
        # extract_msg.html_body 是bytes，需要解码
        email_data_local["html"] = msg.html_body.decode('utf-8', errors='ignore') if msg.html_body else ""
        
        for att in msg.attachments:
            if att.data:
                filename = att.long_filename if att.long_filename else att.short_filename
                if filename:
                    # extract_msg 库通常已经将内联图片处理为附件或直接嵌入HTML
                    # 这里我们将所有图片附件和带有CID的附件都视为可预览图片
                    if att.mime_type and att.mime_type.startswith('image/'):
                        try:
                            # 为图片预览生成Base64 Data URI
                            img = Image.open(io.BytesIO(att.data))
                            buffered = io.BytesIO()
                            img_format = img.format if img.format in ["PNG", "JPEG", "GIF", "BMP"] else "PNG"
                            img.save(buffered, format=img_format)
                            img_str = base64.b64encode(buffered.getvalue()).decode()
                            
                            email_data_local["embedded_images_for_display"].append({
                                "filename": filename,
                                "data_uri": f"data:image/{img_format.lower()};base64,{img_str}",
                                "is_attachment": not bool(att.cid) # 如果有CID，通常是内联；没有CID且是图片，就当做图片附件
                            })
                            # 如果它有CID，通常会被 extract_msg 嵌入到HTML中，这里就不作为普通附件列出
                            if not att.cid:
                                email_data_local["attachments"].append({"filename": filename, "data": att.data, "mime_type": att.mime_type})
                        except Exception as e:
                            st.warning(f"无法预览MSG图片附件 {filename}: {e}")
                    else: # 非图片附件
                        email_data_local["attachments"].append({"filename": filename, "data": att.data, "mime_type": att.mime_type})
        
        # 如果只有HTML正文，尝试将其转换为纯文本作为备用
        if not email_data_local["body"] and email_data_local["html"]:
            soup = BeautifulSoup(email_data_local["html"], 'html.parser')
            email_data_local["body"] = soup.get_text(separator='\n')

    except Exception as e:
        st.error(f"解析 .msg 文件时发生错误: {e}")
        email_data_local["subject"] = "MSG 文件解析失败"
        email_data_local["body"] = f"文件解析时发生错误: {e}"
        # 清空其他数据以避免显示不完整或错误信息
        email_data_local["html"] = ""
        email_data_local["attachments"] = []
        email_data_local["embedded_images_for_display"] = []
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path) # 清理临时文件

    return email_data_local

# --- Streamlit 主应用逻辑 ---
st.markdown('<div class="file-uploader"><h3>上传邮件文件</h3></div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "选择 .eml 或 .msg 文件",
    type=["eml", "msg"],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    file_content = uploaded_file.getvalue()

    with st.spinner("正在解析邮件文件，请稍候..."):
        try:
            if file_ext == ".eml":
                email_data = parse_eml(file_content)
            elif file_ext == ".msg":
                email_data = parse_msg(file_content)
            else:
                st.error("不支持的文件类型。请上传 .eml 或 .msg 文件。")
                email_data["subject"] = "文件类型不支持"
                email_data["body"] = "请上传 .eml 或 .msg 文件。"
            st.success("邮件解析完成！")
        except Exception as e:
            st.error(f"解析文件时发生未知错误: {e}")
            st.info("请确保文件是有效的邮件格式。")
            email_data["subject"] = "文件解析错误"
            email_data["body"] = f"文件解析时发生未知错误: {e}"
else:
    st.info("请上传 .eml 或 .msg 文件以开始预览。")

# --- 显示邮件预览 ---
st.markdown('<div class="preview-section"><h3 class="preview-title">邮件内容预览</h3></div>', unsafe_allow_html=True)

# 邮件头信息
st.markdown(f"""
<div class="email-header">
    <strong>主题:</strong> {email_data["subject"]}<br>
    <strong>发件人:</strong> {email_data["from"]}<br>
    <strong>收件人:</strong> {email_data["to"]}<br>
    <strong>日期:</strong> {email_data["date"]}
</div>
""", unsafe_allow_html=True)

# 邮件正文
st.markdown("<h4>邮件正文:</h4>", unsafe_allow_html=True)
if email_data["html"]:
    # 优先显示清理后的HTML正文
    cleaned_html = clean_html(email_data["html"])
    if cleaned_html: # 只有当清理后HTML不为空时才渲染
        st.components.v1.html(cleaned_html, height=400, scrolling=True)
    else:
        st.warning("HTML正文清理后为空或无法渲染，将显示纯文本正文。")
        st.markdown(f'<div class="email-body-container">{email_data["body"] if email_data["body"] else "HTML正文无法显示且无纯文本正文。"}</div>', unsafe_allow_html=True)
elif email_data["body"]:
    # 如果没有HTML正文，显示纯文本正文
    st.markdown(f'<div class="email-body-container">{email_data["body"]}</div>', unsafe_allow_html=True)
else:
    st.info("邮件没有可显示的文本或HTML正文。")

# 图片预览
st.markdown("<h4>图片预览:</h4>", unsafe_allow_html=True)
if email_data["embedded_images_for_display"]:
    st.markdown('<div class="image-preview-container">', unsafe_allow_html=True)
    
    # 动态计算每行显示的列数，以适应放大后的图片
    # 假设每张图片预览卡片宽约450px + 25px间距 = 475px
    # Streamlit 页面宽度通常在 700px-1000px，取中间值 900px
    # 每行大约能放 900 / 475 = ~1.89 张，所以放 2 张比较合适，或者让它自动换行
    # 这里我们不固定列数，而是让flexbox自动换行，保持更灵活的布局
    
    for i, img_info in enumerate(email_data["embedded_images_for_display"]):
        # 直接在循环中生成每个图片预览项的HTML，让CSS负责布局
        st.markdown(f"""
            <div class="image-preview-item">
                <img src="{img_info['data_uri']}" alt="{img_info['filename']}">
                <p>{img_info['filename']}</p>
                <div class="image-download-button">
                    <a href="{img_info['data_uri']}" download="{img_info['filename']}" style="text-decoration:none;">
                        <button style="background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">下载</button>
                    </a>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True) # 结束容器
else:
    st.info("没有发现可预览的图片（包括内联图片和图片附件）。")

# 附件列表
st.markdown("<h4>附件:</h4>", unsafe_allow_html=True)
if email_data["attachments"]:
    for attachment in email_data["attachments"]:
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.markdown(f'<div class="attachment-card">📎 {attachment["filename"]}</div>', unsafe_allow_html=True)
        with col2:
            st.download_button(
                label="下载",
                data=attachment["data"],
                file_name=attachment["filename"],
                mime=attachment["mime_type"],
                key=f"download_{attachment['filename']}_{attachment['mime_type']}" # 使用更独特的key
            )
else:
    st.info("没有发现普通附件。")

# 可选：调试信息 (在开发时取消注释查看原始解析数据)
# st.markdown("---")
# st.markdown("<h4>调试信息 (Debug Info):</h4>", unsafe_allow_html=True)
# st.json(email_data)