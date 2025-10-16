import streamlit as st

st.title("文本展示示例")
st.header("这是一个二级标题")
st.subheader("这是一个三级标题")

st.write("---") # 分割线

st.write("`st.write()` 是一个非常灵活的函数，可以显示多种内容。")
st.markdown("你可以在 Markdown 中使用 **粗体**、*斜体* 和 [链接](https://streamlit.io)。")
st.caption("这是一个小标题，常用于备注。")

st.code("""
import pandas as pd
df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
st.write(df)
""", language="python")

st.latex(r"""
E=mc^2
""")