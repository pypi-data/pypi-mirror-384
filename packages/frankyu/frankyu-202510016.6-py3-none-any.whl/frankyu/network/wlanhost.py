

aaa = r'''
::netsh wlan start hostednetwork //start hotspot


netsh wlan set hostednetwork mode=allow ssid=intel-mini key=55555555

ping 127.1


netsh wlan start hostednetwork



pause
'''
print(aaa)