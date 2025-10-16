import streamlit as st

st.title("会话状态示例")

# 初始化会话状态变量
if 'counter' not in st.session_state:
    st.session_state.counter = 0

st.write(f"当前计数器值: {st.session_state.counter}")

if st.button("增加计数器"):
    st.session_state.counter += 1
    st.write("计数器已增加！")

if st.button("重置计数器"):
    st.session_state.counter = 0
    st.write("计数器已重置！")

st.write("---")

# 另一个使用会话状态的例子：保存用户输入
st.subheader("保存用户输入")
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

name_input = st.text_input("输入你的名字", value=st.session_state.user_name)

if st.button("保存名字"):
    st.session_state.user_name = name_input
    st.write(f"你的名字已保存为: {st.session_state.user_name}")

st.write("刷新页面或重新运行应用，你会发现保存的名字还在。")