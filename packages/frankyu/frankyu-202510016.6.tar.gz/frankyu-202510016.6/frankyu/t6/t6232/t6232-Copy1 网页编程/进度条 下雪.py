import streamlit as st
import time

st.title("状态和进度示例")

# Spinner
with st.spinner('正在执行耗时操作...'):
    time.sleep(3)
st.success('操作完成！')

# 进度条
st.subheader("进度条")
progress_text = "操作进行中。请稍候。"
my_bar = st.progress(0, text=progress_text)

for percent_complete in range(100):
    time.sleep(0.05)
    my_bar.progress(percent_complete + 1, text=progress_text)
st.success('所有任务已完成！')

# 气球
if st.button("庆祝一下！"):
    st.balloons()

# 下雪
if st.button("下雪！"):
    st.snow()

# Toast
if st.button("显示通知"):
    st.toast('这是一个短暂的通知！')