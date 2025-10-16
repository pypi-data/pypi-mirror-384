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

# 设置页面标题和布局
st.set_page_config(
    page_title="邮件预览器",
    page_icon=":email:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .file-uploader {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .preview-section {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .preview-title {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .email-header {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #3498db;
    }
    .attachment-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        color: white;
    }
    .email-body-container {
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        min-height: 200px;
        max-height: 600px;
        overflow-y: auto;
        background-color: #fff;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.markdown('<div class="header"><h1>📧 邮件预览器</h1></div>', unsafe_allow_html=True)

# 文件上传区域
st.markdown('<div class="file-uploader"><h3>上传邮件文件</h3></div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "选择 .eml 或 .msg 文件",
    type=["eml", "msg"],
    label_visibility="collapsed"
)

# 初始化邮件数据变量
email_data = {
    "subject": "未选择邮件",
    "from": "",
    "to": "",
    "date": "",
    "body": "",
    "html": "",
    "attachments": [],
    "images": []
}

# Function to extract embedded images from HTML (for MSG files, already handled by extract_msg somewhat)
# For EML, this function is used to convert Content-ID images to base64 within the HTML.
def replace_cid_with_base64(html_content, embedded_images):
    for img_info in embedded_images:
        cid = img_info["cid"]
        data_uri = f'data:image/{img_info["type"].lower() if img_info["type"] else "png"};base64,{img_info["data"]}'
        # Use regex to replace all occurrences of cid in src attributes
        html_content = re.sub(rf'src=["\']cid:{re.escape(cid)}["\']', f'src="{data_uri}"', html_content, flags=re.IGNORECASE)
    return html_content

# Function to parse .eml files
def parse_eml(file_content):
    msg = BytesParser(policy=policy.default).parsebytes(file_content)
    
    subject = msg.get("Subject", "无主题")
    from_header = msg.get("From", "未知发件人")
    to_header = msg.get("To", "未知收件人")
    date_header = msg.get("Date", "未知日期")

    body_plain = ""
    body_html = ""
    attachments = []
    embedded_images = []

    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition", "")
        
        # Extract plain text body
        if part.get_content_maintype() == 'text' and content_type == 'text/plain' and 'attachment' not in content_disposition:
            charset = part.get_content_charset()
            try:
                body_plain = part.get_payload(decode=True).decode(charset if charset else 'utf-8', errors='ignore')
            except Exception:
                body_plain = part.get_payload(decode=True).decode('latin-1', errors='ignore') # Fallback
        
        # Extract HTML body
        elif part.get_content_maintype() == 'text' and content_type == 'text/html' and 'attachment' not in content_disposition:
            charset = part.get_content_charset()
            try:
                body_html = part.get_payload(decode=True).decode(charset if charset else 'utf-8', errors='ignore')
            except Exception:
                body_html = part.get_payload(decode=True).decode('latin-1', errors='ignore') # Fallback

        # Handle attachments
        elif "attachment" in content_disposition or part.get_filename():
            filename = part.get_filename()
            if filename:
                try:
                    file_data = part.get_payload(decode=True)
                    attachments.append({"filename": filename, "data": file_data, "mime_type": part.get_content_type()})
                except Exception as e:
                    st.warning(f"无法解析附件 {filename}: {e}")
        # Handle inline images for .eml (Content-ID)
        elif part.get_content_maintype() == 'image' and part.get('Content-ID'):
            cid = part.get('Content-ID').strip('<>')
            try:
                img_data = part.get_payload(decode=True)
                img = Image.open(io.BytesIO(img_data))
                buffered = io.BytesIO()
                # Ensure the format is suitable for base64 (e.g., PNG, JPEG)
                img_format = img.format if img.format in ["PNG", "JPEG", "GIF", "BMP"] else "PNG"
                img.save(buffered, format=img_format)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                embedded_images.append({"cid": cid, "data": img_str, "type": img_format})
            except Exception as e:
                st.warning(f"无法处理内联图片（EML CID: {cid}）: {e}")

    # After parsing all parts, replace CIDs in HTML if any embedded images were found
    if body_html and embedded_images:
        body_html = replace_cid_with_base64(body_html, embedded_images)

    # If only HTML body exists, and plain text is empty, try to convert HTML to plain text
    if not body_plain and body_html:
        # A simple way to get plain text from HTML, more robust solutions exist (e.g., BeautifulSoup)
        body_plain = re.sub('<[^<]+?>', '', body_html)
    
    return {
        "subject": subject,
        "from": from_header,
        "to": to_header,
        "date": date_header,
        "body": body_plain,
        "html": body_html,
        "attachments": attachments,
        "images": embedded_images
    }

# Function to parse .msg files
def parse_msg(file_content):
    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".msg") as tmp_file:
        tmp_file.write(file_content)
        tmp_file_path = tmp_file.name

    try:
        msg = extract_msg.Message(tmp_file_path)
        
        subject = msg.subject if msg.subject else "无主题"
        from_header = msg.sender if msg.sender else "未知发件人"
        to_header = msg.to if msg.to else "未知收件人"
        
        # extract_msg's date format might need reformatting
        date_header = msg.date if msg.date else "未知日期"
        try:
            # Attempt to parse and reformat date for consistency
            date_obj = datetime.strptime(date_header, "%a, %d %b %Y %H:%M:%S %z")
            date_header = date_obj.strftime("%Y-%m-%d %H:%M:%S %Z")
        except ValueError:
            pass # Keep original if parsing fails

        body_plain = msg.body if msg.body else ""
        body_html = msg.html_body.decode('utf-8') if msg.html_body else "" # html_body is bytes

        attachments = []
        for att in msg.attachments:
            if att.data:
                # att.long_filename or att.short_filename
                attachments.append({"filename": att.long_filename if att.long_filename else att.short_filename, "data": att.data, "mime_type": att.mime_type})
        
        # extract_msg handles embedded images by replacing CIDs with base64 data directly in html_body
        # We can extract them if needed for a separate display, but for HTML rendering, they are already inlined.
        embedded_images = []
        for att in msg.attachments:
            if att.cid and att.data:
                try:
                    img = Image.open(io.BytesIO(att.data))
                    buffered = io.BytesIO()
                    img_format = img.format if img.format in ["PNG", "JPEG", "GIF", "BMP"] else "PNG"
                    img.save(buffered, format=img_format)
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    embedded_images.append({"cid": att.cid, "data": img_str, "type": img_format})
                except Exception as e:
                    st.warning(f"无法处理内联图片（MSG CID: {att.cid}）: {e}")

    finally:
        os.remove(tmp_file_path) # Clean up the temporary file

    return {
        "subject": subject,
        "from": from_header,
        "to": to_header,
        "date": date_header,
        "body": body_plain,
        "html": body_html,
        "attachments": attachments,
        "images": embedded_images
    }

# 处理上传的文件
if uploaded_file is not None:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    file_content = uploaded_file.getvalue()

    try:
        if file_ext == ".eml":
            email_data = parse_eml(file_content)
        elif file_ext == ".msg":
            email_data = parse_msg(file_content)
        else:
            st.error("不支持的文件类型。请上传 .eml 或 .msg 文件。")
    except Exception as e:
        st.error(f"解析文件时发生错误: {e}")
        st.info("请确保文件是有效的邮件格式。")

# 显示邮件预览
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
    st.components.v1.html(email_data["html"], height=400, scrolling=True)
elif email_data["body"]:
    st.markdown(f'<div class="email-body-container">{email_data["body"]}</div>', unsafe_allow_html=True)
else:
    st.info("邮件没有可显示的文本或HTML正文。")

# 附件
if email_data["attachments"]:
    st.markdown("<h4>附件:</h4>", unsafe_allow_html=True)
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
                key=f"download_{attachment['filename']}"
            )
else:
    st.markdown("<h4>附件:</h4>", unsafe_allow_html=True)
    st.info("没有发现附件。")

# 调试信息 (可选)
# st.markdown("---")
# st.markdown("<h4>调试信息 (Debug Info):</h4>", unsafe_allow_html=True)
# st.json(email_data)