aaa = "shutdown -s -t 660"

bbb2 = 3600*2

bbb = str(bbb2)

aaa = " ".join(["shutdown -s -t ",bbb])


import os
#os.system(aaa)


import datetime
now = datetime.datetime.now()

endtime = now + datetime.timedelta(seconds=bbb2)

tex = f'''开机时间{now}\n
间隔时间{datetime.timedelta(seconds=bbb2)}\n
关机时间{endtime}'''


with open("1.txt","r+",encoding="utf-8") as f:
    print(tex,file=f)
    


print(tex)






import frankyu.cmd.command_execute as cm
cm.execute_command(aaa)