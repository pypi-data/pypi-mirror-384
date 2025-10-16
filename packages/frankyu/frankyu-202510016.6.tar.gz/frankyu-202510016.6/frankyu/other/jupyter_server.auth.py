

aaa = r"http://intel_lianxiang:7777/login?next=%2Flab%2Ftree%2FOneDrive%2F%25E7%25A7%2581%25E4%25BA%25BA%25E6%2596%2587%25E4%25BB%25B6%25EF%25BC%258Cdengchunying1988%2FDocuments%2Fsb_py%2Ffrankyu"


print(aaa)




#!/usr/bin/env python
# coding: utf-8

# In[1]:


import  frankyu.jupyter as ju

print(r"""
更改工作目录并执行Jupyter Lab命令。

参数:
target_directory (str): 目标工作目录路径。默认是预设的路径。
jupyter_command (str): 启动Jupyter Lab的命令。默认是以无浏览器模式启动的命令。
远程访问
https://blog.csdn.net/sjtu_wyy/article/details/129940701    
!pip install jupyter notebook   
jupyter notebook --generate-config    
from jupyter_server.auth import passwd
passwd()
c.NotebookApp.ip='*' # 就是设置所有ip皆可访问
c.NotebookApp.password ='argon2:$argon2id$v=19$m=10240,t=10,p=8$J8cR4z79uqROE5+id1P9DQ$41KB/tJKRCqo9beQ9N7aQHMhCSQmnSwOrQXVmSbnU7w'  #刚才生成的密文
c.NotebookApp.open_browser = True 
c.NotebookApp.port =7777 #随便指定一个端口
增加到最后文件 jupyter_notebook_config.py
File:      c:\anaconda3\lib\site-packages\frankyu\jupyter.py
Type:      function

import frankyu.jupyter
""")

'''
!pip install jupyter notebook 

!jupyter notebook --generate-config

from jupyter_server.auth import passwd
passwd()
'''


# In[ ]:




