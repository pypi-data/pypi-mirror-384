from setuptools import setup, find_packages
 
setup(
    name='frankyu',
    version='202505009.5',
    packages=find_packages(),
)


'''



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