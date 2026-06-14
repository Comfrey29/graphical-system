#!/usr/bin/env python3
import tkinter as tk
import subprocess
import sys
import os
from utils import ConfigManager, Themes
from topbar import TopBar
from dock import Dock
from window_manager import WindowManager
from file_manager import FileManager
from settings import SettingsApp
from launcher import Launcher
from notifications import Notifications

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

class AlpineDesktop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.root.destroy()

        self.root = tk.Tk()
        self.root.title("Alpine Desktop")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')

        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)

        self.config = ConfigManager()
        self.current_theme = self.config.get('theme', 'dark')
        self.theme = Themes.get(self.current_theme)
        self.wallpaper_path = self.config.get('wallpaper_path', None)
        self.wallpaper_mode = self.config.get('wallpaper_mode', 'scale')

        self.wm = WindowManager(self)
        self.open_windows = []
        self.active_window = None

        self.set_wallpaper(self.wallpaper_path)

        self.notif = Notifications(self)
        self.topbar = TopBar(self)
        self.dock = Dock(self)
        self.launcher = Launcher(self)

        self.bind_shortcuts()

        self.root.deiconify()
        self.root.mainloop()

    def set_wallpaper(self, path=None):
        self.canvas.delete('wallpaper')
        if path and os.path.exists(path):
            self.wallpaper_path = path
            self.config.set('wallpaper_path', path)
            if PIL_OK:
                try:
                    img = Image.open(path)
                    if self.wallpaper_mode == 'center':
                        w, h = img.size
                        x = (self.screen_width - w)//2
                        y = (self.screen_height - h)//2
                        self.wallpaper_image = ImageTk.PhotoImage(img)
                        self.canvas.create_image(x, y, image=self.wallpaper_image, anchor='nw', tags='wallpaper')
                    elif self.wallpaper_mode == 'scale':
                        img = img.resize((self.screen_width, self.screen_height), Image.LANCZOS)
                        self.wallpaper_image = ImageTk.PhotoImage(img)
                        self.canvas.create_image(0, 0, image=self.wallpaper_image, anchor='nw', tags='wallpaper')
                    elif self.wallpaper_mode == 'tile':
                        w, h = img.size
                        for i in range(0, self.screen_width, w):
                            for j in range(0, self.screen_height, h):
                                self.canvas.create_image(i, j, image=ImageTk.PhotoImage(img), anchor='nw', tags='wallpaper')
                except Exception as e:
                    print("Error wallpaper:", e)
            else:
                self.canvas.configure(bg=self.theme['bg'])
        else:
            self.canvas.configure(bg=self.theme['bg'])

    def launch_app(self, cmd):
        if cmd in ('xterm', 'firefox'):
            subprocess.Popen([cmd])
        else:
            subprocess.Popen(cmd, shell=True)

    def open_filemanager(self):
        FileManager(self)

    def open_settings(self):
        SettingsApp(self)

    def show_notification(self, msg):
        self.notif.show(msg)

    def set_active_window(self, win):
        self.active_window = win
        info = self.wm.get_info(win)
        title = info['title'] if info else 'Finder'
        self.topbar.set_title(title)
        self.topbar.update_global_menus(info)

    def update_active_window(self):
        if self.active_window not in self.open_windows:
            self.active_window = None
            self.topbar.set_title('Finder')
            self.topbar.update_global_menus(None)
        else:
            self.set_active_window(self.active_window)

    def bind_shortcuts(self):
        self.root.bind('<Alt-space>', self.launcher.show)
        self.root.bind('<Alt-Tab>', self._alt_tab)

    def _alt_tab(self, event):
        if not self.open_windows:
            return
        try:
            idx = self.open_windows.index(self.active_window) if self.active_window in self.open_windows else -1
        except ValueError:
            idx = -1
        nxt = self.open_windows[(idx + 1) % len(self.open_windows)]
        nxt.deiconify()
        nxt.lift()
        nxt.focus_set()
        self.set_active_window(nxt)

    def lock_screen(self):
        lock = tk.Toplevel(self.root)
        lock.attributes('-fullscreen', True)
        lock.attributes('-topmost', True)
        lock.configure(bg='black')
        tk.Label(lock, text='Pantalla bloquejada\nPrem Escape per tornar', fg='white', bg='black', font=('Helvetica', 20)).pack(expand=True)
        lock.bind('<Escape>', lambda e: lock.destroy())
        lock.focus_set()

    def restart_session(self):
        self.root.destroy()
        os.execv(sys.executable, ['python'] + sys.argv)

    def shutdown(self):
        from tkinter import messagebox
        if messagebox.askyesno('Apagar', 'Segur que vols apagar?'):
            subprocess.Popen(['poweroff'])

if __name__ == '__main__':
    AlpineDesktop()
