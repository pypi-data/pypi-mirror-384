import streamlit as st
import os
import tempfile
from email import policy
from email.parser import BytesParser
import extract_msg
from PIL import Image
import io
import base64
import re
from datetime import datetime
from bs4 import BeautifulSoup
import bleach
import mimetypes # 用于更准确地推断MIME类型

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

    /* Streamlit 按钮样式覆盖 */
    /* 注意：Streamlit的按钮通常由其内部JS渲染，直接用CSS覆盖可能有限 */
    /* 这里尝试修改通用按钮样式 */
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
        max-width: 450px; /* 放大卡片 */
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
        max-height: 360px; /* 限制图片高度 */
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
# 在全局作用域定义，但会在文件上传时重新初始化
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
        # 优先使用'lxml'解析器，如果未安装则回退到'html.parser'
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except Exception:
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

# --- 辅助函数：HTML内容清理 (更严格的版本，专注于电子邮件地址作为标签名) ---
def clean_html(html_content):
    """
    使用BeautifulSoup和Bleach清理HTML内容，移除script/style标签，
    并限制允许的标签和属性，以防止无效标签名错误。
    这个版本更专注于处理电子邮件地址被误认为标签名的问题。
    """
    if not html_content:
        return ""
    try:
        # Step 1: 激进的预处理，专门处理电子邮件地址被误解析为非法标签名的模式。
        # 这种模式形如 <user@domain> 或 <something_else@domain>
        # HTML标签名不能包含 @ 符号。
        # 将 <user@domain.com> 替换为 &lt;user@domain.com&gt;
        # 这样浏览器就不会尝试将其解析为HTML标签了。
        
        # 这是一个更通用的版本，捕获任何看起来像标签，但内容包含 '@' 符号的字符串。
        # HTML标签名不允许包含 '@'。
        pattern_email_as_tag = re.compile(r'<([^>]+\@[^>]+)>')
        html_content = pattern_email_as_tag.sub(lambda m: f"&lt;{m.group(1)}&gt;", html_content)
        
        if pattern_email_as_tag.search(html_content):
             st.warning("预处理：已将包含'@'的疑似非法HTML标签转换为实体。")

        # 同时，保留上一个版本中对所有非法标签名的通用处理，以防万一
        def _replace_invalid_tag_like_string_general(match):
            content = match.group(1)
            # 检查 content 是否是一个合法的HTML标签名（不含斜杠）
            # 或者 content 后面跟着斜杠 / ，表示闭合标签
            if re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_.-]*', content) or \
               re.fullmatch(r'/[a-zA-Z][a-zA-Z0-9_.-]*', content):
                return match.group(0) # 合法标签名，保留
            else:
                # 非法标签名，将其内容转义
                st.warning(f"预处理：发现并转义疑似非法HTML标签 '{content}'。")
                return f"&lt;{content}&gt;"

        # 匹配 <ANYTHING>，然后通过函数判断是否为合法标签名
        html_content = re.sub(r'<([^>]+)>', _replace_invalid_tag_like_string_general, html_content)
        
        # Step 2: 使用BeautifulSoup进行初步解析和修复
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except Exception:
            st.warning("lxml解析器不可用或出错，回退到html.parser。")
            soup = BeautifulSoup(html_content, 'html.parser')

        # 移除 script 和 style 标签
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
        
        # 遍历所有标签，检查标签名是否合法
        for tag in list(soup.find_all(True)): # 使用 list() 避免在迭代时修改集合
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_.-]*$', tag.name):
                st.warning(f"BeautifulSoup修复：发现非法HTML标签名 '{tag.name}'，尝试移除标签并保留内容。")
                try:
                    tag.unwrap() # 将标签移除，但保留其内容
                except Exception as unwrap_e:
                    st.error(f"unwrap非法标签失败: {unwrap_e}. 尝试用文本替代。")
                    tag.replace_with(str(tag.encode('utf-8', errors='ignore').decode('utf-8')))
        
        cleaned_soup_str = str(soup)

        # 定义允许的HTML标签和属性。这个列表可以根据需求调整。
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
        # 如果清理过程出现任何错误，返回空字符串，让主逻辑回退到显示纯文本
        st.error(f"HTML 清理失败 (clean_html function): {e}. 将尝试显示纯文本。")
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
                        if mime_type and mime_type.startswith('image/'):
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
            try:
                # 优先使用'lxml'解析器，如果未安装则回退到'html.parser'
                try:
                    soup = BeautifulSoup(email_data_local["html"], 'lxml')
                except Exception:
                    soup = BeautifulSoup(email_data_local["html"], 'html.parser')
                email_data_local["body"] = soup.get_text(separator='\n')
            except Exception as e:
                st.warning(f"从HTML提取纯文本失败: {e}")


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
    增加了对mime_type缺失的健壮性处理，并增加了调试信息。
    """
    email_data_local = {
        "subject": "无主题", "from": "未知发件人", "to": "未知收件人",
        "date": "未知日期", "body": "", "html": "",
        "attachments": [], "embedded_images_for_display": []
    }
    
    tmp_file_path = None
    msg_obj = None # 定义 msg_obj 以便在 finally 中关闭

    try:
        # 将上传的文件内容写入临时文件，供 extract_msg 处理
        with tempfile.NamedTemporaryFile(delete=False, suffix=".msg") as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        msg_obj = extract_msg.Message(tmp_file_path) # 使用 msg_obj 变量
        
        email_data_local["subject"] = msg_obj.subject if msg_obj.subject else "无主题"
        email_data_local["from"] = msg_obj.sender if msg_obj.sender else "未知发件人"
        email_data_local["to"] = msg_obj.to if msg_obj.to else "未知收件人"
        
        email_data_local["date"] = msg_obj.date if msg_obj.date else "未知日期"
        try:
            # 尝试解析并重新格式化日期以保持一致性
            date_obj = datetime.strptime(email_data_local["date"], "%a, %d %b %Y %H:%M:%S %z")
            email_data_local["date"] = date_obj.strftime("%Y-%m-%d %H:%M:%S %Z")
        except ValueError:
            pass # 如果解析失败，保留原始日期字符串

        email_data_local["body"] = msg_obj.body if msg_obj.body else ""
        
        # 检查 html_body 属性是否存在
        if hasattr(msg_obj, 'html_body') and msg_obj.html_body:
            email_data_local["html"] = msg_obj.html_body.decode('utf-8', errors='ignore')
        else:
            email_data_local["html"] = ""
        
        st.write("--- 附件解析调试信息 ---") 
        if not msg_obj.attachments: 
            st.write("未在MSG文件中找到任何附件。") 
        
        for i, att in enumerate(msg_obj.attachments): 
            st.write(f"正在处理附件 {i+1}:") 
            st.write(f"  原始对象类型: {type(att)}") 
            st.write(f"  hasattr(att, 'long_filename'): {hasattr(att, 'long_filename')}") 
            st.write(f"  att.long_filename: {getattr(att, 'long_filename', 'N/A')}") 
            st.write(f"  hasattr(att, 'short_filename'): {hasattr(att, 'short_filename')}") 
            st.write(f"  att.short_filename: {getattr(att, 'short_filename', 'N/A')}") 
            st.write(f"  hasattr(att, 'name'): {hasattr(att, 'name')}") 
            st.write(f"  att.name: {getattr(att, 'name', 'N/A')}") 
            st.write(f"  hasattr(att, 'mime_type'): {hasattr(att, 'mime_type')}") 
            st.write(f"  att.mime_type: {getattr(att, 'mime_type', 'N/A')}") 
            st.write(f"  att.data exists: {bool(att.data)}") 
            st.write(f"  att.data length: {len(att.data) if att.data else 0} bytes") 


            if att.data: 
                # 更健壮地获取附件文件名
                filename = None 
                if hasattr(att, 'long_filename') and att.long_filename: 
                    filename = att.long_filename 
                elif hasattr(att, 'short_filename') and att.short_filename: 
                    filename = att.short_filename 
                elif hasattr(att, 'name') and att.name: 
                    filename = att.name 
                
                if not filename: 
                    filename = f"unknown_attachment_{len(email_data_local['attachments'])}.bin" 
                    st.warning(f"无法获取附件文件名，使用默认名称: {filename}") 

                # 健壮地获取 mime_type
                # 优先使用附件自带的mime_type
                mime_type = 'application/octet-stream' # 默认值
                if hasattr(att, 'mime_type') and att.mime_type: 
                    mime_type = att.mime_type 
                else:
                    if filename: 
                        # 使用 mimetypes 库进行更标准的推断
                        guessed_mime_type, _ = mimetypes.guess_type(filename) 
                        if guessed_mime_type: 
                            mime_type = guessed_mime_type 
                        else:
                            ext = os.path.splitext(filename)[1].lower() 
                            if ext in ['.jpg', '.jpeg']: 
                                mime_type = 'image/jpeg' 
                            elif ext == '.png': 
                                mime_type = 'image/png' 
                            elif ext == '.gif': 
                                mime_type = 'image/gif' 
                            elif ext == '.bmp': 
                                mime_type = 'image/bmp' 
                            elif ext == '.pdf': 
                                mime_type = 'application/pdf' 
                            elif ext == '.doc' or ext == '.docx': 
                                mime_type = 'application/msword' 
                            elif ext == '.xls' or ext == '.xlsx': 
                                mime_type = 'application/vnd.ms-excel' 
                            elif ext == '.ppt' or ext == '.pptx': 
                                mime_type = 'application/vnd.ms-powerpoint' 
                            elif ext == '.txt': 
                                mime_type = 'text/plain' 
                    st.warning(f"附件 '{filename}' 缺少 MIME 类型，尝试推断为: {mime_type}")


                if filename: # 确保filename不为空
                    if mime_type.startswith('image/'): 
                        try:
                            img = Image.open(io.BytesIO(att.data)) 
                            buffered = io.BytesIO() 
                            img_format = img.format if img.format in ["PNG", "JPEG", "GIF", "BMP"] else "PNG" 
                            img.save(buffered, format=img_format) 
                            img_str = base64.b64encode(buffered.getvalue()).decode() 
                            
                            email_data_local["embedded_images_for_display"].append({ 
                                "filename": filename, 
                                "data_uri": f"data:image/{img_format.lower()};base64,{img_str}", 
                                "is_attachment": not bool(getattr(att, 'cid', None)) # 检查是否有cid属性
                            })
                            # 只有当它不是内联图片时，才作为普通附件列出
                            if not hasattr(att, 'cid') or not att.cid: 
                                email_data_local["attachments"].append({"filename": filename, "data": att.data, "mime_type": mime_type}) 
                        except Exception as e:
                            st.warning(f"无法预览MSG图片附件 {filename}: {e}") 
                    else: # 非图片附件
                        email_data_local["attachments"].append({"filename": filename, "data": att.data, "mime_type": mime_type}) 
        
        st.write("--- 附件处理结果 ---") 
        st.write(f"普通附件数量: {len(email_data_local['attachments'])}") 
        for att in email_data_local['attachments']: 
            st.write(f"  - 文件名: {att['filename']}, MIME: {att['mime_type']}, 大小: {len(att['data'])} bytes") 
        st.write(f"可显示图片数量: {len(email_data_local['embedded_images_for_display'])}") 
        for img in email_data_local['embedded_images_for_display']: 
            st.write(f"  - 文件名: {img['filename']}, 是附件图片: {img['is_attachment']}") 

        # 如果只有HTML正文，尝试将其转换为纯文本作为备用
        if not email_data_local["body"] and email_data_local["html"]: 
            try:
                try: 
                    soup = BeautifulSoup(email_data_local["html"], 'lxml') 
                except Exception: 
                    soup = BeautifulSoup(email_data_local["html"], 'html.parser') 
                email_data_local["body"] = soup.get_text(separator='\n') 
            except Exception as e: 
                st.warning(f"从HTML提取纯文本失败: {e}") 

    except Exception as e: 
        st.error(f"解析 .msg 文件时发生错误: {e}") 
        email_data_local["subject"] = "MSG 文件解析失败" 
        email_data_local["body"] = f"文件解析时发生错误: {e}" 
        if "html_body" not in str(e).lower(): 
             email_data_local["html"] = "" 
        email_data_local["attachments"] = [] 
        email_data_local["embedded_images_for_display"] = [] 
    finally:
        if msg_obj: 
            try: 
                msg_obj.close() 
            except Exception as e: 
                st.warning(f"关闭MSG文件句柄失败: {e}") 
        
        if tmp_file_path and os.path.exists(tmp_file_path): 
            try: 
                os.remove(tmp_file_path) 
            except OSError as e: 
                st.error(f"[清理警告] 无法删除临时文件: {tmp_file_path}. 文件可能仍在使用中或权限问题: {e}") 
                st.info("请尝试关闭所有相关程序或手动删除该文件。") 

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

    # 在这里初始化 email_data，确保每次上传文件时都是新的状态
    email_data = {
        "subject": "未选择邮件", "from": "", "to": "", "date": "",
        "body": "", "html": "", "attachments": [], "embedded_images_for_display": []
    }

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
            
            # 只有在没有致命文件系统错误时才显示成功
            # 改进条件判断，排除所有已知错误消息，包括 HTML 渲染错误
            if not ("文件解析时发生未知错误: [WinError 32]" in email_data["body"] or \
                    "MSG 文件解析失败" in email_data["subject"] or \
                    "EML 文件解析失败" in email_data["subject"] or \
                    "渲染HTML正文失败" in email_data["body"] # 检查HTML正文中是否有错误信息
                    ):
                st.success("邮件解析完成！")

        except Exception as e:
            # 捕获顶层未被内部解析函数处理的异常
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
        try:
            st.components.v1.html(cleaned_html, height=400, scrolling=True)
        except Exception as e:
            # 这是关键：如果 st.components.v1.html 仍抛出错误，
            # 我们在 Python 端捕获并显示友好信息，而不是让浏览器自己弹警告
            st.error(f"渲染HTML正文失败: {e}. 这通常表示HTML中仍存在浏览器不兼容的元素。将显示纯文本正文。")
            st.markdown(f'<div class="email-body-container">{email_data["body"] if email_data["body"] else "HTML正文无法渲染且无纯文本正文。"}</div>', unsafe_allow_html=True)
    else:
        # 如果HTML清理后为空，但有纯文本正文，则显示纯文本
        if email_data["body"]:
            st.warning("HTML正文清理后为空或无法渲染，将显示纯文本正文。")
            st.markdown(f'<div class="email-body-container">{email_data["body"]}</div>', unsafe_allow_html=True)
        else:
            st.info("HTML正文无法显示且无纯文本正文。")
elif email_data["body"]:
    # 如果没有HTML正文，显示纯文本正文
    st.markdown(f'<div class="email-body-container">{email_data["body"]}</div>', unsafe_allow_html=True)
else:
    st.info("邮件没有可显示的文本或HTML正文。")

# --- 显示附件和内联图片 ---
if email_data["attachments"] or email_data["embedded_images_for_display"]:
    st.markdown('<div class="preview-section"><h3 class="preview-title">附件和内联图片</h3></div>', unsafe_allow_html=True)
    
    if email_data["embedded_images_for_display"]:
        st.markdown("<h5>图片预览:</h5>", unsafe_allow_html=True)
        # 为每个图片创建一个容器，以便图片和下载按钮能更好地对齐
        for img_info in email_data["embedded_images_for_display"]:
            try:
                # 使用一个 Streamlit container 来包裹每个图片预览项和其下载按钮
                with st.container(border=True): # border=True 给每个图片预览加个边框
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <img src="{img_info['data_uri']}" alt="{img_info['filename']}" style="max-width: 100%; height: auto; max-height: 300px; object-fit: contain; border-radius: 8px; margin-bottom: 12px; border: 1px solid #f0f0f0;">
                        <p style="font-size: 0.95em; word-break: break-all; margin: 0; color: #555;">{img_info['filename']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    # 将下载按钮直接放在 container 内，它会出现在图片下方
                    st.download_button(
                        label=f"下载 {img_info['filename']}",
                        data=base64.b64decode(img_info['data_uri'].split(',')[1]),
                        file_name=img_info['filename'],
                        mime=img_info['data_uri'].split(';')[0].split(':')[1],
                        key=f"img_download_{img_info['filename']}_{hash(img_info['data_uri'])}" # 确保唯一key
                    )
            except Exception as e:
                st.warning(f"无法为图片 {img_info['filename']} 生成预览或下载按钮: {e}")
    
    if email_data["attachments"]:
        st.markdown("<h5>其他附件:</h5>", unsafe_allow_html=True)
        for attachment in email_data["attachments"]:
            if attachment['mime_type'] and attachment['mime_type'].startswith('image/'):
                # 附件中的图片已在embedded_images_for_display中处理，这里跳过
                continue
            
            # 使用 st.columns 更好地控制布局，将文件名和下载按钮放在同一行
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                st.markdown(f"""
                <div class="attachment-card" style="border:none; box-shadow:none; padding: 0.5rem 0;">
                    <span>📁 {attachment['filename']} ({attachment['mime_type']})</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.download_button(
                    label="下载",
                    data=attachment["data"],
                    file_name=attachment["filename"],
                    mime=attachment["mime_type"],
                    key=f"att_download_{attachment['filename']}"
                )
else:
    st.info("邮件中没有附件或内联图片。")