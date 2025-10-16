# 定义一个多行字符串变量 `aaa`，用于存储一系列批处理命令
aaa = r"""

::C:  # 切换到 C 盘根目录

::cd C:\Users\frank_yu\py  # 切换到用户目录 `C:\Users\frank_yu\py`

::C:\Users\Public\Python39\Scripts\jupyter-lab.exe  # 启动 Jupyter Lab

::lab_py10.bat  # 执行批处理文件 `lab_py10.bat`

::C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome_proxy.exe  --profile-directory=Default --app-id=gmifgajiejkkbgfbegjkojkdeibadhdl
# 启动 Chrome 浏览器的应用模式，使用指定的配置文件和应用 ID

chcp 65001  # 设置命令提示符的代码页为 UTF-8

D:  # 切换到 D 盘

::cd  "D:\Users\t4_kelly\OneDrive\私人文件，dengchunying1988\Documents\sb_py"
# 切换到目标目录（已注释）

cd "D:\t3\OneDrive\私人文件，dengchunying1988\Documents\sb_py"
# 切换到实际使用的目标目录

C:\anaconda3\Scripts\jupyter-lab.exe --no-browser
# 启动 Jupyter Lab，并禁用默认浏览器自动打开

C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome_proxy.exe  --profile-directory=Default --app-id=gmifgajiejkkbgfbegjkojkdeibadhdl
# 再次启动 Chrome 浏览器的应用模式，使用指定的配置文件和应用 ID

"""

# 打印变量 `aaa` 的内容
print(aaa)

# 等待用户输入，防止脚本立即退出
input()