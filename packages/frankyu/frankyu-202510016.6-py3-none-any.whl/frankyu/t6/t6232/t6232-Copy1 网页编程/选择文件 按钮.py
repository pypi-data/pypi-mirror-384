import streamlit as st
import datetime

st.title("用户输入示例")

# 按钮
if st.button("点我！"):
    st.write("你点击了按钮！")

# 复选框
agree = st.checkbox("我同意条款和条件")
if agree:
    st.write("太棒了！你同意了。")

# 单选按钮
genre = st.radio(
    "你喜欢哪种电影类型？",
    ["喜剧", "剧情", "动作", "科幻"]
)
st.write("你选择了:", genre)

# 下拉选择框
option = st.selectbox(
    "你最喜欢的颜色是什么？",
    ("蓝色", "红色", "绿色", "黄色")
)
st.write("你最喜欢的颜色是:", option)

# 多选下拉框
options = st.multiselect(
    "你喜欢哪些水果？",
    ["苹果", "香蕉", "橘子", "葡萄", "草莓"]
)
st.write("你选择了:", options)

# 滑块
age = st.slider("你的年龄是？", 0, 100, 25)
st.write("你的年龄是:", age)

# 范围滑块
values = st.select_slider(
    "选择一个范围的数字",
    options=list(range(0, 101)),
    value=(25, 75)
)
st.write("你选择的范围是:", values)

# 文本输入框
name = st.text_input("你的名字是？", "请输入你的名字")
st.write("你好，", name)

# 数字输入框
number = st.number_input("输入一个数字", min_value=0, max_value=100, value=50)
st.write("你输入的数字是:", number)

# 多行文本输入框
message = st.text_area("输入你的消息", "这里可以输入多行文本...")
st.write("你的消息是:", message)

# 日期选择器
d = st.date_input(
    "选择一个日期",
    datetime.date(2023, 1, 1)
)
st.write("你选择的日期是:", d)

# 时间选择器
t = st.time_input('设置一个时间', datetime.time(8, 45))
st.write('你设置的时间是:', t)

# 文件上传
uploaded_file = st.file_uploader("上传一个文件")
if uploaded_file is not None:
    # 可以对上传的文件进行处理，例如读取内容
    file_details = {"文件名": uploaded_file.name, "文件类型": uploaded_file.type, "文件大小": uploaded_file.size}
    st.write(file_details)
    # 如果是文本文件，可以读取其内容
    # string_data = uploaded_file.read().decode("utf-8")
    # st.write(string_data)

# 颜色选择器
color = st.color_picker('选择一个颜色', '#00f900')
st.write('你选择的颜色是:', color)