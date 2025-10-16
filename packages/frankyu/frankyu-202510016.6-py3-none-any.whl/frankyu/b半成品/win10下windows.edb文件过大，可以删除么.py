#!/usr/bin/env python
# coding: utf-8

# In[7]:


"""Windows.edb是Windows Search索引文件，主要用于提供内容索引、属性缓存以及文件、电子邮件和其他内容的搜索结果。由于Windows系统默认会对文件进行索引以加快搜索速度，所有与索引有关的数据都存储在这个edb文件中。随着使用时间的增长，Windows.edb文件可能会变得非常大，占用大量磁盘空间‌
1
2
。

删除Windows.edb文件的步骤
‌停止Windows Search服务‌：
打开“命令提示符”（以管理员身份运行）。
输入以下命令来停止Windows Search服务：net stop wsearch。
输入以下命令来禁用Windows Search服务的自动启动：sc config wsearch start= disabled。
‌删除Windows.edb文件‌：
导航到文件路径：C:\ProgramData\Microsoft\Search\Data\Applications\Windows。
删除Windows.edb文件。
‌重新启动Windows Search服务‌：
输入以下命令来启动Windows Search服务：net start wsearch。
输入以下命令来恢复Windows Search服务的自动启动：sc config wsearch start= delayed-auto‌
1
2
。
删除后是否会重新生成
删除Windows.edb文件后，只要Windows Search服务继续运行，该文件会重新生成。因此，如果希望彻底删除该文件并阻止其重新生成，需要停止使用Windows Search服务或完全禁用该服务‌
3
。
"""


# In[2]:


aaa = "net stop wsearch"


# In[1]:


bbb = r"sc config wsearch start= disabled"


# In[4]:


ccc = r"net start wsearch"


# In[5]:


eee = "sc config wsearch start= delayed-auto"


# In[10]:


for i in [aaa,bbb]:
    import os
    import time
    
    os.system(i)
    time.sleep(10)


# In[11]:


for i in [ccc,ddd]:
    import os
    import time
    
    os.system(i)
    time.sleep(10)


# In[ ]:




