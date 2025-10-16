import streamlit as st

aaa = st.file_uploader("12")

if aaa:
    print(aaa.type) # 直接访问 'type' 属性