import time
time.sleep(5)



import win32gui
import win32con
 
def minimize_all_windows():
    def _enum_windows_proc(hwnd, param):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE) & win32con.WS_VISIBLE:
            win32gui.SendMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_MINIMIZE, 0)
 
    win32gui.EnumWindows(_enum_windows_proc, 0)
    import time
    time.sleep(2)
    import os
    os.system("cqzy")
 
minimize_all_windows()