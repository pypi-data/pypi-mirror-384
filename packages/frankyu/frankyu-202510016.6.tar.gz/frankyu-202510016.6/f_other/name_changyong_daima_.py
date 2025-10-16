pipy=r'''
from setuptools import setup, find_packages

setup(
    name="your-package-name",     # 包名（PyPI 中唯一）
    version="0.1.0",              # 版本号（每次上传需更新）
    author="Your Name",
    author_email="your@email.com",
    description="A short description",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/your-package",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',     # 指定 Python 版本要求
    install_requires=[],         # 依赖列表（可选）
)


your_package/
  ├── your_package/       # 包源码目录
  │   └── __init__.py
  ├── setup.py            # 或 setup.cfg、pyproject.toml（用于配置包信息）
  ├── README.md           # 项目说明
  └── LICENSE             # 开源协议



pip install --upgrade setuptools wheel  # 构建工具
pip install --upgrade twine            # 安全上传工具



python setup.py sdist bdist_wheel


pip install build
python -m build


# 上传到正式 PyPI
twine upload dist/*

# 若测试，上传到 TestPyPI
twine upload --repository testpypi dist/*



[distutils]
index-servers =
  pypi
  testpypi

[pypi]
username = __token__
password = your-pypi-token-here  # 使用 Token 更安全

[testpypi]
repository = https://test.pypi.org/legacy/
username = your-testpypi-username
password = your-testpypi-password



PyPI 恢復代碼 5018fff87a5847f1 c59e2a33294e8399 fc07992e00cd58a5 bba2ffcdfdd76bf2 265b6344f21b54fd 53ea452df256398 5c4


pypi-AgEIcHlwaS5vcmcCJDZiNDgyNjVkLTc4ZTEtNDJiMC1iYWZmLTkzODhlMTExODBlZAACD1sxLFsiZnJhbmt5dSJdXQACLFsyLFsiYjIwNzZmMmUtODViYy00ODIxLTg0MzEtZmM2ZjI5MjAzMDE0Il1dAAAGIIWz1eVSRGckx3qW9F-vH91F5l6PCS9DjHKJe08MhNoZ


pypi-AgEIcHlwaS5vcmcCJDk1YmQ2YzE5LThjYjMtNGM0NC05NDQ0LTc2YzVkYzZjYmVlMAACD1sxLFsiZnJhbmt5dSJdXQACLFsyLFsiYjIwNzZmMmUtODViYy00ODIxLTg0MzEtZmM2ZjI5MjAzMDE0Il1dAAAGIHr0bU-4XXkdto70spXbebadMypu4cPvGClhY2lVXfdf



your_project/
├── your_package/
│   ├── __init__.py
│   └── your_code.py
├── pyproject.toml
├── README.md
├── LICENSE
└── setup.py（可选，若不使用 pyproject.toml）

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "your-package-name"  # 包名，需唯一
version = "0.1.0"          # 版本号
authors = [
    { name = "Your Name", email = "your.email@example.com" },
]
description = "A short description of your package"
readme = "README.md"
requires-python = ">=3.7"
dependencies = [
    "pywin32>=306",  # 示例依赖
]


# Your Package Name
A Python package to do something awesome.

## Installation
pip install your-package-name

## Usage
import your_package
your_package.some_function()



MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy...


twine upload --repository testpypi dist/*




'''

ren_gong_zi_neng = r'''
@echo off
chcp 65001

:: 设置代码页为UTF-8，以支持显示中文等Unicode字符
chcp 65001

:: 检查Chrome浏览器可执行文件是否存在于联想台式机的默认路径
if exist C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe (
    :: 如果存在，则输出 "這裡是聯想台式機"
    echo 這裡是聯想台式機
) else (
    :: 如果不存在，则输出 "這裡不是聯想台式機"
    echo 這裡不是聯想台式機
)

:: 启动 Chrome 浏览器，并配置用户数据目录、代理服务器、最大化窗口，并打开 DeepSeek Chat 网站
start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chrome0823 ^
    --proxy-server=10.7.1.181:8080 ^
    --start-maximized ^
    https://chat.deepseek.com/

:: 启动 Chrome 浏览器，并配置用户数据目录、代理服务器、最大化窗口，并打开 Gemini (Google Bard) 网站 (繁体中文界面)
start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chrome0823 ^
    --proxy-server=10.7.1.181:8080 ^
    --start-maximized ^
    https://gemini.google.com/app?hl=zh_TW

:: 启动 Chrome 浏览器，并配置用户数据目录、代理服务器、最大化窗口，并打开 Felo.ai 搜索页面
start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chrome0823 ^
    --proxy-server=10.7.1.181:8080 ^
    --start-maximized ^
    https://felo.ai/search/nyMrd4pevCm9hvWWf5dGso

:: 启动 Chrome 浏览器，并配置用户数据目录、代理服务器、最大化窗口，并打开 Perplexity AI 搜索 "yan zhou tian qi" (亚洲天气)
start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chrome0823 ^
    --proxy-server=10.7.1.181:8080 ^
    --start-maximized ^
    https://www.perplexity.ai/search/yan-zhou-tian-qi-NVSToZB1QEy9qcH8qJ0G4g

:: 启动 Chrome 浏览器，并配置用户数据目录、代理服务器、最大化窗口，并打开 Mistral AI Chat 网站
start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chrome0823 ^
    --proxy-server=10.7.1.181:8080 ^
    --start-maximized ^
    https://chat.mistral.ai/chat/88e16360-4415-4796-be30-e42b7baa89e4

:: 启动 Chrome 浏览器，并配置用户数据目录、代理服务器、最大化窗口，并打开 GitHub Copilot 页面
start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chrome0823 ^
    --proxy-server=10.7.1.181:8080 ^
    --start-maximized ^
    https://github.com/copilot/c/bc585d28-fa09-45e2-bce5-5349c4384095

:: 启动 Chrome 浏览器，并配置用户数据目录、代理服务器、最大化窗口，并打开 Grok Chat 网站
start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chrome0823 ^
    --proxy-server=10.7.1.181:8080 ^
    --start-maximized ^
    https://grok.com/chat/b54fd9f5-0df3-43f8-b4b0-cb9338192667

:: 启动 Chrome 浏览器，并配置用户数据目录、代理服务器、最大化窗口，并打开 Tongyi Qianwen (阿里云通义千问) 网站
start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chrome0823 ^
    --proxy-server=10.7.1.181:8080 ^
    --start-maximized ^
    https://tongyi.aliyun.com/?sessionId=109e818a368344d98eb81baaf78c2eb0

:: 启动 Chrome 浏览器，并配置用户数据目录、代理服务器、最大化窗口，并打开 Tongyi Qianwen (阿里云通义千问) 网站
start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chrome0823 ^
    --proxy-server=10.7.1.181:8080 ^
    --start-maximized ^
    https://kimi.moonshot.cn/





:: 启动 Chrome 浏览器，并配置用户数据目录、不使用代理服务器、最大化窗口，并打开 Cici.com 网站
::start "" "C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe" ^
    --user-data-dir=D:\del\s8chromet224 ^
    --start-maximized ^
    https://www.cici.com/

:: 延迟等待，避免脚本过快退出 (以下 ping 命令用于简单延迟)
ping 127.0.0.1 >nul
ping 127.0.0.1 >nul
ping 127.0.0.1 >nul

'''


chrome = r'''

echo off
chcp 65001

if exist C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe    (echo 這裡是聯想台式機 ) else ( 這裡不是聯想台式機

   )
   


C:\Users\frank_yu\AppData\Local\Google\Chrome\Application\chrome.exe --user-data-dir=D:\del\s8chrome0823202408  --proxy-server=10.7.1.181:8080   --start-maximized   https://photos.google.com/

ping 127.0.0.1 >nul


ping 127.0.0.1 >nul


ping 127.0.0.1 >nul


'''

gbc9 = r'''


#import frankyu

from frankyu import kill_program ,frankyu

print("20250313")


frankyu.daoJiShi_t2(3)

#m = "swriter mspaint every".split(" ")
m = []

m = m + ["SnippingTool"]

m = m + ["team"]

m = m + ["edge", "chrome", "outlook", "excel", "POWERPNT", "YoudaoDict", "Picasa3", "WinRAR", "AcroRd32", "Xmind"]

# m = m  + ["WeChat","WeChatStore"]

# m = m +  ["Everything" ]


m = m + ["iCloud", "notepad"]

m = m + ["cmd"]
m = m + ["pycha"]

m = m + ["WINWORD", ]

m = m + ["Foxmail", "wemeetapp", "WhatsApp", ]
m = m + ["onedrive"]

for i in m:


    #frankyu.gbc(i)
    kill_program.kill_program(i)
    

frankyu.daoJiShi_t2(30)

 



'''



