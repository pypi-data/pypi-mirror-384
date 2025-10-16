aaa = r'''
 /etc/systemd/logind.conf

sudo nano /etc/systemd/logind.conf

HandleLidSwitch=ignore

sudo systemctl restart systemd-logind


cp  /etc/systemd/logind.conf    2.
txt

get 2.txt

找到如下两行：

ini
深色版本
#HandleLidSwitch=suspend
#HandleLidSwitchExternalPower=suspend
修改为：

ini
深色版本
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitch：控制笔记本合上盖子时的行为。
HandleLidSwitchExternalPower：接通电源时合上盖子的行为。
将它们都设为 ignore，表示“什么都不做”。


sudo cp  3.txt   /etc/systemd/login
d.conf


sudo systemctl restart systemd-logind


'''
