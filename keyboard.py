import tkinter as tk
from tkinter import ttk
import time
import ctypes
import threading
import pystray
from PIL import Image
import sys
import winreg

# 状态检测
def is_capslock_on():
    return ctypes.windll.user32.GetKeyState(0x14) & 1

def is_numlock_on():
    return ctypes.windll.user32.GetKeyState(0x90) & 1

# 悬浮通知（不卡顿、不排队）
toast_window = None
toast_label = None

def show_notify(title, msg):
    global toast_window, toast_label
    try:
        if toast_window is not None:
            toast_label.config(text=msg)
            toast_window.lift()
            return

        toast_window = tk.Tk()
        toast_window.overrideredirect(True)
        toast_window.attributes("-topmost", True)
        toast_window.attributes("-alpha", 0.9)

        screen_w = toast_window.winfo_screenwidth()
        screen_h = toast_window.winfo_screenheight()
        x = screen_w - 220
        y = screen_h - 120
        toast_window.geometry(f"200x40+{x}+{y}")

        toast_label = ttk.Label(
            toast_window,
            text=msg,
            font=("微软雅黑", 11),
            background="#ffffff",
            padding=5
        )
        toast_label.pack(expand=True, fill="both")

        toast_window.after(400, toast_window.destroy)
        toast_window.mainloop()

        toast_window = None
        toast_label = None

    except:
        pass

# 后台监听
def monitor_loop(update_ui):
    last_caps = is_capslock_on()
    last_num = is_numlock_on()
    while True:
        time.sleep(0.1)
        caps = is_capslock_on()
        num = is_numlock_on()

        if caps != last_caps:
            last_caps = caps
            show_notify("键盘状态", "大写锁定 已打开" if caps else "大写锁定 已关闭")
            update_ui()

        if num != last_num:
            last_num = num
            show_notify("键盘状态", "小键盘 已打开" if num else "小键盘 已关闭")
            update_ui()

# 开机自启
def is_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "KeyboardLight")
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

def set_startup(enable):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
    if enable:
        path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
        winreg.SetValueEx(key, "KeyboardLight", 0, winreg.REG_SZ, f'"{path}"')
    else:
        try:
            winreg.DeleteValue(key, "KeyboardLight")
        except FileNotFoundError:
            pass
    winreg.CloseKey(key)

# ====================== 主界面 + 托盘 ======================
def create_ui():
    root = tk.Tk()
    root.title("键盘状态指示灯")
    root.geometry("300x180")
    root.resizable(False, False)

    caps_label = ttk.Label(root, text="大写锁定：检测中...", font=("微软雅黑", 12))
    caps_label.pack(pady=5)

    num_label = ttk.Label(root, text="小键盘：检测中...", font=("微软雅黑", 12))
    num_label.pack(pady=5)

    def update_ui():
        caps_state = is_capslock_on()
        num_state = is_numlock_on()
        caps_label.config(text=f"大写锁定：{'已打开✅' if caps_state else '已关闭❌'}")
        num_label.config(text=f"小键盘：{'已打开✅' if num_state else '已关闭❌'}")

    startup_var = tk.BooleanVar(value=is_startup())
    def toggle_startup():
        set_startup(startup_var.get())

    startup_check = ttk.Checkbutton(root, text="开机自启", variable=startup_var, command=toggle_startup)
    startup_check.pack(pady=10)

    # 启动监听线程
    monitor_thread = threading.Thread(target=monitor_loop, args=(update_ui,), daemon=True)
    monitor_thread.start()

    update_ui()

    # ------------------- 托盘核心（绝对稳定，不报错、不重复）-------------------
    tray_icon = None

    def create_icon():
        return Image.new('RGB', (16, 16), color=(0, 120, 215))

    def show_window(icon, item):
        root.deiconify()

    def quit_app(icon, item):
        nonlocal tray_icon
        if tray_icon:
            tray_icon.stop()
        root.destroy()

    def run_tray():
        nonlocal tray_icon
        tray_icon = pystray.Icon(
            "KeyboardState",
            create_icon(),
            "键盘状态指示灯",
            menu=pystray.Menu(
                pystray.MenuItem("显示窗口", show_window),
                pystray.MenuItem("退出", quit_app)
            )
        )
        tray_icon.run()

    def on_close():
        nonlocal tray_icon
        root.withdraw()
        if tray_icon is None:
            threading.Thread(target=run_tray, daemon=True).start()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == '__main__':
    create_ui()