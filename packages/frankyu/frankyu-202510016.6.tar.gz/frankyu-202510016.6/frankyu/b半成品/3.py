import os

def jupyter_lab(target_directory=r"D:\t3\OneDrive\私人文件，dengchunying1988\Documents\sb_py", 
                        jupyter_command=r"C:\Users\Public\Python310\Scripts\jupyter-lab.exe --no-browser"):
    """
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
    """
    # 打印当前的工作目录
    print("当前工作目录: " + os.getcwd())
    
    # 更改到目标工作目录
    os.chdir(target_directory)
    
    # 确认更改后的工作目录
    print("更改后的工作目录: " + os.getcwd())
    
    # 执行启动Jupyter Lab的命令
    os.system(jupyter_command)

# 示例调用函数
if __name__ == "__main__":
    jupyter_lab()