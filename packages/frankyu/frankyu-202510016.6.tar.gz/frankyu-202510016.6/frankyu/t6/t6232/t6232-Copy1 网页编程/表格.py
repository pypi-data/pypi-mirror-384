import streamlit as st
import pandas as pd
import numpy as np

st.title("数据展示示例")

df = pd.DataFrame(
    np.random.randn(10, 5),
    columns=('col %d' % i for i in range(5))
)

st.subheader("使用 `st.dataframe()` 展示数据帧 (交互式)")
st.dataframe(df)

st.subheader("使用 `st.table()` 展示静态表格")
st.table(df.head())

st.subheader("使用 `st.metric()` 展示关键指标")
st.metric(label="温度", value="28°C", delta="1.2°C")
st.metric(label="湿度", value="65%", delta="-2%")