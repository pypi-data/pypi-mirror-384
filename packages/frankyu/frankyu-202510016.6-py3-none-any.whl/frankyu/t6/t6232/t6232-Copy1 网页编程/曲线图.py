import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.title("Matplotlib 图表示例")

# 生成一些数据
x = np.linspace(0, 10, 100)
y = np.sin(x)

# 创建 Matplotlib 图表
fig, ax = plt.subplots()
ax.plot(x, y)
ax.set_title("正弦波")
ax.set_xlabel("X轴")
ax.set_ylabel("Y轴")

# 在 Streamlit 中显示图表
st.pyplot(fig)

st.write("---")

# 交互式图表示例
st.subheader("交互式 Matplotlib 图表")
n_points = st.slider("选择数据点数量", 10, 200, 100)
freq = st.slider("选择频率", 1.0, 10.0, 2.0)

x_interactive = np.linspace(0, 10, n_points)
y_interactive = np.sin(x_interactive * freq)

fig_interactive, ax_interactive = plt.subplots()
ax_interactive.plot(x_interactive, y_interactive)
ax_interactive.set_title(f"正弦波 (点数: {n_points}, 频率: {freq})")
ax_interactive.set_xlabel("X轴")
ax_interactive.set_ylabel("Y轴")

st.pyplot(fig_interactive)