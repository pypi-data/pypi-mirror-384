import streamlit as st
import pandas as pd
import time

st.title("缓存机制示例")

# 缓存数据加载
@st.cache_data
def load_data():
    st.write("正在加载数据 (仅第一次运行或数据更新时显示)")
    time.sleep(2) # 模拟耗时的数据加载
    data = pd.DataFrame({
        'col1': [1, 2, 3, 4],
        'col2': [10, 20, 30, 40]
    })
    return data

df = load_data()
st.subheader("缓存的数据:")
st.dataframe(df)

st.write("---")

# 缓存计算结果
@st.cache_data
def expensive_computation(a, b):
    st.write(f"正在执行耗时计算: {a} + {b} (仅当输入改变时显示)")
    time.sleep(1)
    return a + b

num1 = st.number_input("输入第一个数字", value=10)
num2 = st.number_input("输入第二个数字", value=20)

result = expensive_computation(num1, num2)
st.subheader(f"计算结果: {result}")

st.write("尝试改变数字，观察 '正在执行耗时计算' 何时出现。")