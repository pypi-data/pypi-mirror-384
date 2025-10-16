import streamlit as st
from PIL import Image # Pillow 库用于图像处理

st.title("媒体展示示例")

# 图片
st.subheader("图片展示")
# 假设你有一个名为 'example.jpg' 的图片文件
# 如果没有，你可以从网上下载一张图片并保存到你的脚本同目录下
try:
    image = Image.open('example.jpg')
    st.image(image, caption='这是一张示例图片', use_column_width=True)
except FileNotFoundError:
    st.warning("请在当前目录下放置一个 'example.jpg' 文件来查看图片示例。")
    st.image("https://www.streamlit.io/images/brand/streamlit-logo-primary-dark.png", caption="Streamlit Logo", use_column_width=True)

# 音频
st.subheader("音频播放")
audio_file = open('example.mp3', 'rb') # 假设你有一个名为 'example.mp3' 的音频文件
audio_bytes = audio_file.read()
st.audio(audio_bytes, format='audio/mp3')
audio_file.close()

# 视频
st.subheader("视频播放")
video_file = open('example.mp4', 'rb') # 假设你有一个名为 'example.mp4' 的视频文件
video_bytes = video_file.read()
st.video(video_bytes)
video_file.close()