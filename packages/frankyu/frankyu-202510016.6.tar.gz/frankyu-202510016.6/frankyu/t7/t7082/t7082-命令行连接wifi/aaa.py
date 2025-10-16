aaa = r'''

nmcli
network-manager

sudo ip link set wlx488ad237935b up

nmcli device wifi rescan ifname wlx488ad237935b

nmcli device wifi list ifname wlx488ad237935b

nmcli device wifi connect "xiaomi880125" password "55555555" ifname wlx488ad237935b


'''
