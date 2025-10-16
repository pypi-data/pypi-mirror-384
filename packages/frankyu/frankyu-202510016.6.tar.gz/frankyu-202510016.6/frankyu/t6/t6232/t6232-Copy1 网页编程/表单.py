import streamlit as st

st.title("表单示例")

with st.form("my_form"):
    st.write("在表单中输入你的信息")
    name = st.text_input("姓名")
    email = st.text_input("邮箱")
    message = st.text_area("留言")

    # Every form must have a submit button.
    submitted = st.form_submit_button("提交")

    if submitted:
        st.write("表单已提交！")
        st.write(f"姓名: {name}")
        st.write(f"邮箱: {email}")
        st.write(f"留言: {message}")