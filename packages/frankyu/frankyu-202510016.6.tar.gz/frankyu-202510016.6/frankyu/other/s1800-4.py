aaa = "shutdown -s -t 660"

bbb2 = 3600*10

bbb = str(bbb2)

aaa = " ".join([" shutdown -a &    ping 127.1   &   shutdown -s -t ",bbb])


import os
#os.system(aaa)


import datetime
now = datetime.datetime.now()

endtime = now + datetime.timedelta(seconds=bbb2)

tex = f'''开机时间{now}\n
间隔时间{datetime.timedelta(seconds=bbb2)}\n
关机时间{endtime}'''


with open("1.txt","w",encoding="utf-8") as f:
    print(tex,file=f)
    


print(tex)






import frankyu.cmd.command_execute as cm
cm.execute_command(aaa)