import streamlit as st

st.title("布局示例")

# 侧边栏
st.sidebar.header("侧边栏")
st.sidebar.text_input("侧边栏输入框", "你好")

# 多列布局
st.header("多列布局")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("这是第一列")
    st.button("按钮1")
with col2:
    st.write("这是第二列")
    st.button("按钮2")
with col3:
    st.write("这是第三列")
    st.button("按钮3")

# 选项卡布局
st.header("选项卡布局")
tab1, tab2, tab3 = st.tabs(["介绍", "数据", "图表"])
with tab1:
    st.write("这是介绍页面的内容。")
with tab2:
    st.write("这里可以展示数据表格。")
with tab3:
    st.write("这里可以展示数据图表。")

# 容器
st.header("容器")
with st.container(border=True):
    st.write("这个容器包含了一段文本和一个滑块。")
    st.slider("容器内的滑块", 0, 10)

# 可折叠区域
st.header("可折叠区域")
with st.expander("点击展开更多信息"):
    st.write("这里是一些隐藏起来的信息。")
    st.image("https://static.streamlit.io/examples/cat.jpg", width=20)