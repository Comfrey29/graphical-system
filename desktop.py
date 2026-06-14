#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpine Desktop - macOS-style desktop environment for Alpine Linux aarch64
Single-file Tkinter application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import json
import subprocess
import threading
import time
import glob
import re
import math
import shutil
import sys

# Try to import PIL for wallpaper scaling
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class WindowManager:
    """Handles internal toplevel windows with macOS-style decorations."""
    def __init__(self, desktop):
        self.desktop = desktop
        self.windows = []  # list of dicts: {'toplevel', 'title', 'decorations'}

    def add_window(self, toplevel, title="Sens títol", app_icon=None):
        toplevel.overrideredirect(True)
        toplevel.configure(bg=self.desktop.themes[self.desktop.current_theme]['bg'])
        # Create decoration frame inside toplevel
        deco_frame = tk.Frame(toplevel, bg=self.desktop.themes[self.desktop.current_theme]['window_title_bg'], height=28)
        deco_frame.pack(fill='x', side='top')
        deco_frame.pack_propagate(False)

        # Title label
        title_label = tk.Label(deco_frame, text=title, fg=self.desktop.themes[self.desktop.current_theme]['window_title_fg'],
                               bg=self.desktop.themes[self.desktop.current_theme]['window_title_bg'], font=('Helvetica', 10, 'bold'))
        title_label.pack(side='left', padx=5)

        # Buttons (close, minimize, maximize)
        btn_frame = tk.Frame(deco_frame, bg=self.desktop.themes[self.desktop.current_theme]['window_title_bg'])
        btn_frame.pack(side='right', padx=5)

        close_btn = tk.Button(btn_frame, text='●', fg=self.desktop.themes[self.desktop.current_theme]['button_close'],
                              bg=self.desktop.themes[self.desktop.current_theme]['window_title_bg'], bd=0, font=('Helvetica', 12, 'bold'),
                              command=lambda: self.close_window(toplevel))
        close_btn.pack(side='left', padx=2)
        minimize_btn = tk.Button(btn_frame, text='●', fg=self.desktop.themes[self.desktop.current_theme]['button_minimize'],
                                 bg=self.desktop.themes[self.desktop.current_theme]['window_title_bg'], bd=0, font=('Helvetica', 12, 'bold'),
                                 command=lambda: self.minimize_window(toplevel))
        minimize_btn.pack(side='left', padx=2)
        maximize_btn = tk.Button(btn_frame, text='●', fg=self.desktop.themes[self.desktop.current_theme]['button_maximize'],
                                 bg=self.desktop.themes[self.desktop.current_theme]['window_title_bg'], bd=0, font=('Helvetica', 12, 'bold'),
                                 command=lambda: self.maximize_window(toplevel))
        maximize_btn.pack(side='left', padx=2)

        # Bind dragging on decoration
        deco_frame.bind('<Button-1>', lambda e, w=toplevel: self.start_drag(w, e))
        deco_frame.bind('<B1-Motion>', lambda e, w=toplevel: self.do_drag(w, e))
        deco_frame.bind('<Double-Button-1>', lambda e, w=toplevel: self.maximize_window(w))

        # Container for content
        content = tk.Frame(toplevel, bg=self.desktop.themes[self.desktop.current_theme]['bg'])
        content.pack(fill='both', expand=True)

        # Track
        window_info = {
            'toplevel': toplevel,
            'title': title,
            'deco_frame': deco_frame,
            'content': content,
            'title_label': title_label,
            'minimized': False,
            'maximized': False,
            'prev_geom': None
        }
        self.windows.append(window_info)

        # Focus handling
        toplevel.bind('<FocusIn>', lambda e, w=toplevel: self.on_focus(w))
        toplevel.bind('<FocusOut>', lambda e: self.desktop.update_topbar_title())
        toplevel.protocol("WM_DELETE_WINDOW", lambda w=toplevel: self.close_window(w))

        return window_info

    def start_drag(self, win, event):
        win._drag_data = {'x': event.x_root, 'y': event.y_root}

    def do_drag(self, win, event):
        if hasattr(win, '_drag_data'):
            dx = event.x_root - win._drag_data['x']
            dy = event.y_root - win._drag_data['y']
            x = win.winfo_x() + dx
            y = win.winfo_y() + dy
            win.geometry(f'+{x}+{y}')
            win._drag_data = {'x': event.x_root, 'y': event.y_root}

    def close_window(self, win):
        for w in self.windows:
            if w['toplevel'] == win:
                if win in self.desktop.open_windows:
                    self.desktop.open_windows.remove(win)
                win.destroy()
                self.windows.remove(w)
                break
        self.desktop.update_active_window()

    def minimize_window(self, win):
        win.withdraw()
        for w in self.windows:
            if w['toplevel'] == win:
                w['minimized'] = True
        self.desktop.update_active_window()

    def maximize_window(self, win):
        for w in self.windows:
            if w['toplevel'] == win:
                if not w['maximized']:
                    w['prev_geom'] = win.geometry()
                    # Maximize: fill screen minus top bar and dock
                    top_height = self.desktop.topbar.winfo_height()
                    dock_height = 70
                    win.geometry(f"{self.desktop.screen_width}x{self.desktop.screen_height - top_height - dock_height}+0+{top_height}")
                    w['maximized'] = True
                else:
                    if w['prev_geom']:
                        win.geometry(w['prev_geom'])
                    w['maximized'] = False
                break

    def on_focus(self, win):
        self.desktop.active_window = win
        self.desktop.update_topbar_title()

    def get_window_by_toplevel(self, win):
        for w in self.windows:
            if w['toplevel'] == win:
                return w
        return None

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
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))

        # Canvas for wallpaper
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)

        # Config directory
        self.config_dir = os.path.expanduser('~/.config/alpine-de')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, 'config.json')
        self.config = self.load_config()

        # Theme
        self.current_theme = self.config.get('theme', 'dark')
        self.themes = {
            'dark': {
                'topbar_bg': '#2c2c2e',
                'dock_bg': '#4c4c4e',
                'window_title_bg': '#3c3c3e',
                'window_title_fg': '#ffffff',
                'button_close': '#ff5f57',
                'button_minimize': '#febc2e',
                'button_maximize': '#28c840',
                'text_color': '#ffffff',
                'bg': '#1e1e1e',
                'listbox_bg': '#2d2d2d',
                'entry_bg': '#3d3d3d',
                'notebook_bg': '#2c2c2e',
                'tab_bg': '#3c3c3e',
                'active_tab_bg': '#505050'
            },
            'light': {
                'topbar_bg': '#e0e0e0',
                'dock_bg': '#d0d0d0',
                'window_title_bg': '#f0f0f0',
                'window_title_fg': '#000000',
                'button_close': '#ff5f57',
                'button_minimize': '#febc2e',
                'button_maximize': '#28c840',
                'text_color': '#000000',
                'bg': '#ffffff',
                'listbox_bg': '#f0f0f0',
                'entry_bg': '#ffffff',
                'notebook_bg': '#e0e0e0',
                'tab_bg': '#f0f0f0',
                'active_tab_bg': '#d0d0d0'
            }
        }

        # Wallpaper
        self.wallpaper_image = None
        self.wallpaper_mode = self.config.get('wallpaper_mode', 'scale')
        self.wallpaper_path = self.config.get('wallpaper_path', None)
        self.set_wallpaper(self.wallpaper_path)

        # Window manager
        self.wm = WindowManager(self)
        self.open_windows = []  # list of toplevels
        self.active_window = None

        # Top bar and dock as Toplevel windows
        self.topbar = None
        self.dock = None
        self.dock_icons = []  # list of dicts: {'frame', 'label', 'app_name'}
        self.dock_open_apps = set()
        self.dock_zoom_enabled = self.config.get('dock_zoom', True)
        self.dock_position = self.config.get('dock_position', 'bottom')

        self.setup_topbar()
        self.setup_dock()

        # Launcher
        self.launcher_win = None
        self.setup_launcher()

        # Shortcuts
        self.bind_shortcuts()

        # Clock and battery update
        self.update_clock()
        self.update_battery()

        # Notification queue
        self.notification_queue = []
        self.notification_win = None
        self.notification_timer = None

        self.root.deiconify()
        self.root.mainloop()

    # --- Configuration ---
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def apply_theme(self):
        theme = self.themes[self.current_theme]
        self.root.configure(bg=theme['bg'])
        self.canvas.configure(bg=theme['bg'])

    # --- Wallpaper ---
    def set_wallpaper(self, path=None):
        self.canvas.delete('wallpaper')
        if path and os.path.exists(path):
            self.wallpaper_path = path
            self.config['wallpaper_path'] = path
            self.save_config()
            if PIL_AVAILABLE:
                try:
                    img = Image.open(path)
                    mode = self.wallpaper_mode
                    cw = self.screen_width
                    ch = self.screen_height
                    if mode == 'center':
                        # Resize canvas to image size centered
                        w, h = img.size
                        x = (cw - w)//2
                        y = (ch - h)//2
                        self.wallpaper_image = ImageTk.PhotoImage(img)
                        self.canvas.create_image(x, y, image=self.wallpaper_image, anchor='nw', tags='wallpaper')
                    elif mode == 'scale':
                        img = img.resize((cw, ch), Image.LANCZOS)
                        self.wallpaper_image = ImageTk.PhotoImage(img)
                        self.canvas.create_image(0, 0, image=self.wallpaper_image, anchor='nw', tags='wallpaper')
                    elif mode == 'tile':
                        # Tile the image
                        w, h = img.size
                        for i in range(0, cw, w):
                            for j in range(0, ch, h):
                                self.canvas.create_image(i, j, image=ImageTk.PhotoImage(img), anchor='nw', tags='wallpaper')
                        self.wallpaper_image = None  # Not stored as single image
                except Exception as e:
                    print(f"Error setting wallpaper: {e}")
            else:
                print("PIL not available, cannot set wallpaper. Please install pillow.")
        else:
            self.canvas.configure(bg=self.themes[self.current_theme]['bg'])

    # --- Top Bar ---
    def setup_topbar(self):
        self.topbar = tk.Toplevel(self.root)
        self.topbar.overrideredirect(True)
        self.topbar.attributes('-topmost', True)
        self.topbar.configure(bg=self.themes[self.current_theme]['topbar_bg'])
        # Semi-transparent not directly possible per-widget; we'll use alpha on the whole topbar
        try:
            self.topbar.attributes('-alpha', 0.95)
        except:
            pass
        self.topbar.geometry(f"{self.screen_width}x28+0+0")

        # Left: Apple logo
        apple_frame = tk.Frame(self.topbar, bg=self.themes[self.current_theme]['topbar_bg'])
        apple_frame.pack(side='left', padx=5)
        self.apple_label = tk.Label(apple_frame, text='', fg='white', bg=self.themes[self.current_theme]['topbar_bg'],
                                    font=('Helvetica', 12, 'bold'), cursor='hand2')
        self.apple_label.pack()
        self.apple_label.bind('<Button-1>', self.show_apple_menu)

        # Center: App title (dynamic) + optional global menu
        self.topbar_center_frame = tk.Frame(self.topbar, bg=self.themes[self.current_theme]['topbar_bg'])
        self.topbar_center_frame.pack(side='left', expand=True, fill='x')
        self.app_title_label = tk.Label(self.topbar_center_frame, text="Finder", fg='white',
                                        bg=self.themes[self.current_theme]['topbar_bg'], font=('Helvetica', 10))
        self.app_title_label.pack(pady=2)

        # Global menu placeholder (Fitxer, Edita, Visualitza)
        self.menu_frame = tk.Frame(self.topbar, bg=self.themes[self.current_theme]['topbar_bg'])
        self.menu_frame.pack(side='left', padx=10)
        self.menu_buttons = []
        for m in ["Fitxer", "Edita", "Visualitza"]:
            mb = tk.Menubutton(self.menu_frame, text=m, fg='white', bg=self.themes[self.current_theme]['topbar_bg'],
                               activebackground='#505050', font=('Helvetica', 10), bd=0, padx=5)
            mb.menu = tk.Menu(mb, tearoff=0)
            mb['menu'] = mb.menu
            mb.pack(side='left')
            self.menu_buttons.append(mb)
        self.update_global_menus()  # initially empty

        # Right: time, battery, network
        self.topbar_right_frame = tk.Frame(self.topbar, bg=self.themes[self.current_theme]['topbar_bg'])
        self.topbar_right_frame.pack(side='right', padx=10)
        self.clock_label = tk.Label(self.topbar_right_frame, text="", fg='white',
                                    bg=self.themes[self.current_theme]['topbar_bg'], font=('Helvetica', 9))
        self.clock_label.pack(side='left', padx=5)
        self.battery_label = tk.Label(self.topbar_right_frame, text="🔋 --%", fg='white',
                                      bg=self.themes[self.current_theme]['topbar_bg'], font=('Helvetica', 9))
        self.battery_label.pack(side='left', padx=5)
        self.network_label = tk.Label(self.topbar_right_frame, text="📶", fg='white',
                                      bg=self.themes[self.current_theme]['topbar_bg'], font=('Helvetica', 9))
        self.network_label.pack(side='left', padx=5)

    def show_apple_menu(self, event):
        popup = tk.Menu(self.root, tearoff=0)
        popup.add_command(label="Quant a aquest Mac", command=lambda: messagebox.showinfo("Quant a", "Alpine Desktop 1.0"))
        popup.add_command(label="Preferències del Sistema", command=self.open_settings)
        popup.add_separator()
        popup.add_command(label="Bloquejar pantalla", command=self.lock_screen)
        popup.add_command(label="Reiniciar sessió", command=self.restart_session)
        popup.add_command(label="Apagar", command=self.shutdown)
        try:
            popup.tk_popup(event.x_root, event.y_root)
        finally:
            popup.grab_release()

    def lock_screen(self):
        # Simple lock: cover screen
        lock = tk.Toplevel(self.root)
        lock.attributes('-fullscreen', True)
        lock.attributes('-topmost', True)
        lock.configure(bg='black')
        label = tk.Label(lock, text="Pantalla bloquejada\nPrem Escape per tornar", fg='white', bg='black', font=('Helvetica', 20))
        label.pack(expand=True)
        lock.bind('<Escape>', lambda e: lock.destroy())
        lock.focus_set()

    def restart_session(self):
        self.root.destroy()
        os.execv(sys.executable, ['python'] + sys.argv)

    def shutdown(self):
        # In real usage, execute `poweroff` maybe with sudo.
        if messagebox.askyesno("Apagar", "Segur que vols apagar l'equip?"):
            subprocess.Popen(["poweroff"], shell=False)

    def update_topbar_title(self):
        if self.active_window and self.active_window in self.open_windows:
            winfo = self.wm.get_window_by_toplevel(self.active_window)
            if winfo:
                self.app_title_label.config(text=winfo['title'])
        else:
            self.app_title_label.config(text="Finder")

    def update_global_menus(self):
        # Only for internal windows
        active = self.active_window
        winfo = self.wm.get_window_by_toplevel(active) if active else None
        for mb in self.menu_buttons:
            mb.menu.delete(0, 'end')
        if winfo:
            # Example actions
            if self.menu_buttons[0]['text'] == 'Fitxer':
                self.menu_buttons[0].menu.add_command(label="Tancar finestra", command=lambda w=active: self.wm.close_window(w))
                self.menu_buttons[0].menu.add_command(label="Sortir", command=lambda: self.root.destroy())
            if self.menu_buttons[1]['text'] == 'Edita':
                self.menu_buttons[1].menu.add_command(label="Desfer", command=lambda: None)
                self.menu_buttons[1].menu.add_command(label="Refer", command=lambda: None)
            if self.menu_buttons[2]['text'] == 'Visualitza':
                self.menu_buttons[2].menu.add_command(label="Maximitzar", command=lambda w=active: self.wm.maximize_window(w))
        else:
            # Default menus for Finder? leave empty
            pass

    def update_clock(self):
        now = time.localtime()
        # Catalan day abbreviation
        days_ca = ['dll.', 'dma.', 'dmc.', 'dij.', 'div.', 'dss.', 'dmg.']
        day = days_ca[now.tm_wday]
        date_str = f"{day} {now.tm_mday}/{now.tm_mon}"
        time_str = f"{now.tm_hour:02d}:{now.tm_min:02d}"
        self.clock_label.config(text=f"{date_str} {time_str}")
        self.root.after(30000, self.update_clock)  # every 30 seconds

    def update_battery(self):
        capacity = None
        try:
            # Check typical battery paths
            for batt in glob.glob('/sys/class/power_supply/BAT*/capacity'):
                with open(batt, 'r') as f:
                    capacity = int(f.read().strip())
                break
        except:
            pass
        if capacity is not None:
            self.battery_label.config(text=f"🔋 {capacity}%")
        else:
            self.battery_label.config(text="🔋 ---%")
        # Network icon (just a static symbol for simplicity)
        self.network_label.config(text="📶")
        self.root.after(60000, self.update_battery)  # every minute

    # --- Dock ---
    def setup_dock(self):
        self.dock = tk.Toplevel(self.root)
        self.dock.overrideredirect(True)
        self.dock.attributes('-topmost', True)
        self.dock.configure(bg=self.themes[self.current_theme]['dock_bg'])
        try:
            self.dock.attributes('-alpha', 0.8)
        except:
            pass
        dock_width = 600
        self.dock.geometry(f"{dock_width}x70+{(self.screen_width-dock_width)//2}+{self.screen_height-70}")

        self.dock_canvas = tk.Canvas(self.dock, bg=self.themes[self.current_theme]['dock_bg'], highlightthickness=0)
        self.dock_canvas.pack(fill='both', expand=True)

        # Icons
        icons_def = [
            ('📁', 'Finder', self.open_filemanager),
            ('▶', 'Terminal', lambda: self.launch_app('xterm')),
            ('🌐', 'Firefox', lambda: self.launch_app('firefox')),
            ('⚙️', 'Settings', self.open_settings),
            ('🗑️', 'Trash', self.empty_trash)
        ]

        self.dock_icons = []
        for emoji, name, command in icons_def:
            self.add_dock_icon(emoji, name, command)

        # Bind zoom effect
        self.dock_canvas.bind('<Motion>', self.dock_motion)
        self.dock_canvas.bind('<Leave>', self.dock_leave)
        self.dock_canvas.bind('<Button-1>', self.dock_click)
        self.dock_canvas.bind('<Button-3>', self.dock_right_click)
        self.dock_canvas.bind('<B1-Motion>', self.dock_drag)
        self.dock_canvas.bind('<ButtonRelease-1>', self.dock_drop)

        # Bounce animation support
        self.dock_bounce_ids = {}

    def add_dock_icon(self, emoji, name, command):
        icon_data = {
            'emoji': emoji,
            'name': name,
            'command': command,
            'label': None,
            'x': 0, 'y': 20,
            'size': 48,
            'open': False
        }
        # Draw label on canvas
        label = tk.Label(self.dock_canvas, text=emoji, font=('Helvetica', 48), bg=self.themes[self.current_theme]['dock_bg'],
                         fg='white', cursor='hand2')
        label.bind('<Button-1>', lambda e, d=icon_data: self.dock_icon_press(d))
        label.bind('<Button-3>', lambda e, d=icon_data: self.dock_right_click_icon(e, d))
        icon_data['label'] = label
        self.dock_icons.append(icon_data)
        self.arrange_dock_icons()

    def arrange_dock_icons(self):
        # Position icons centered horizontally inside dock canvas
        canvas_width = self.dock_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 600
        total_icons = len(self.dock_icons)
        spacing = 80
        total_width = total_icons * spacing
        start_x = (canvas_width - total_width) // 2 + spacing // 2
        for i, icon in enumerate(self.dock_icons):
            x = start_x + i * spacing
            icon['x'] = x
            self.dock_canvas.create_window(x, 35, window=icon['label'], anchor='center')
            # Blue dot under open apps
            if icon['open']:
                self.dock_canvas.create_oval(x-4, 60, x+4, 68, fill='#007aff', outline='', tags=f"dot_{i}")
            else:
                self.dock_canvas.delete(f"dot_{i}")

    def dock_icon_press(self, icon_data):
        # Launch app
        icon_data['command']()
        # Set open status
        icon_data['open'] = True
        self.dock_open_apps.add(icon_data['name'])
        self.arrange_dock_icons()
        # Bounce animation
        self.bounce_icon(icon_data)

    def bounce_icon(self, icon_data):
        # Simple bounce: move label up and down 3 times
        label = icon_data['label']
        original_y = 35
        def bounce(count=0):
            if count >= 6:
                self.dock_canvas.coords(label, icon_data['x'], original_y)
                return
            delta = -10 if count % 2 == 0 else 10
            new_y = original_y + delta
            self.dock_canvas.coords(label, icon_data['x'], new_y)
            self.dock_canvas.after(100, bounce, count+1)
        bounce()

    def dock_right_click_icon(self, event, icon_data):
        popup = tk.Menu(self.root, tearoff=0)
        popup.add_command(label="Opcions", command=lambda: None)
        popup.add_command(label="Sortir", command=lambda: self.quit_app(icon_data['name']))
        try:
            popup.tk_popup(event.x_root, event.y_root)
        finally:
            popup.grab_release()

    def quit_app(self, app_name):
        # For now, just mark as not open
        self.dock_open_apps.discard(app_name)
        for icon in self.dock_icons:
            if icon['name'] == app_name:
                icon['open'] = False
        self.arrange_dock_icons()

    def empty_trash(self):
        trash_dir = os.path.expanduser('~/.local/share/Trash/files')
        if os.path.exists(trash_dir):
            if messagebox.askyesno("Paperera", "Vols buidar la paperera?"):
                shutil.rmtree(trash_dir)
                os.makedirs(trash_dir, exist_ok=True)

    def dock_motion(self, event):
        if not self.dock_zoom_enabled:
            return
        canvas = self.dock_canvas
        for icon in self.dock_icons:
            label = icon['label']
            distance = abs(event.x - icon['x'])
            max_size = 64
            min_size = 48
            if distance < 60:
                size = max_size - (distance / 60) * (max_size - min_size)
            else:
                size = min_size
            font = ('Helvetica', int(size))
            label.config(font=font)

    def dock_leave(self, event):
        for icon in self.dock_icons:
            icon['label'].config(font=('Helvetica', 48))

    def dock_click(self, event):
        pass  # handled by label

    # Drag & drop reorder (simplified)
    def dock_drag(self, event):
        pass

    def dock_drop(self, event):
        pass

    # --- Launcher (Spotlight) ---
    def setup_launcher(self):
        self.launcher_win = None

    def show_launcher(self, event=None):
        if self.launcher_win and self.launcher_win.winfo_exists():
            self.launcher_win.lift()
            return
        self.launcher_win = tk.Toplevel(self.root)
        self.launcher_win.overrideredirect(True)
        self.launcher_win.attributes('-topmost', True)
        self.launcher_win.configure(bg='#3d3d3d')
        w, h = 500, 60
        x = (self.screen_width - w) // 2
        y = self.screen_height // 4
        self.launcher_win.geometry(f"{w}x{h}+{x}+{y}")
        self.launcher_entry = tk.Entry(self.launcher_win, font=('Helvetica', 14), bg='#5a5a5a', fg='white',
                                       insertbackground='white', bd=0, relief='flat')
        self.launcher_entry.pack(fill='x', padx=10, pady=10)
        self.launcher_entry.focus_set()
        self.launcher_entry.bind('<KeyRelease>', self.search_launcher)
        self.launcher_entry.bind('<Down>', self.launcher_navigate_down)
        self.launcher_entry.bind('<Up>', self.launcher_navigate_up)
        self.launcher_entry.bind('<Return>', self.launcher_execute)
        self.launcher_entry.bind('<Escape>', lambda e: self.launcher_win.destroy())
        self.launcher_results = []
        self.launcher_listbox = None
        self.launcher_listbox_index = -1

    def search_launcher(self, event):
        query = self.launcher_entry.get().strip().lower()
        if not query:
            if self.launcher_listbox:
                self.launcher_listbox.destroy()
                self.launcher_listbox = None
            self.launcher_win.geometry("500x60")
            return
        # Search .desktop files
        results = []
        desktop_files = glob.glob('/usr/share/applications/*.desktop')
        for df in desktop_files:
            try:
                with open(df, 'r', encoding='utf-8') as f:
                    content = f.read()
                name_match = re.search(r'^Name=(.*)$', content, re.MULTILINE)
                exec_match = re.search(r'^Exec=(.*)$', content, re.MULTILINE)
                if name_match and exec_match:
                    name = name_match.group(1)
                    cmd = exec_match.group(1).split()[0]  # simple
                    if query in name.lower() or query in cmd.lower():
                        results.append((name, cmd))
            except:
                pass
        # Also system PATH commands
        paths = os.environ.get('PATH', '').split(':')
        for p in paths:
            if os.path.isdir(p):
                try:
                    for f in os.listdir(p):
                        full = os.path.join(p, f)
                        if os.access(full, os.X_OK) and query in f.lower():
                            results.append((f, full))
                except:
                    pass
        # Remove duplicates
        seen = set()
        unique = []
        for name, cmd in results:
            if (name, cmd) not in seen:
                seen.add((name, cmd))
                unique.append((name, cmd))
        self.launcher_results = unique[:10]  # limit
        if not self.launcher_listbox:
            self.launcher_win.geometry("500x300")
            self.launcher_listbox = tk.Listbox(self.launcher_win, bg=self.themes[self.current_theme]['listbox_bg'],
                                               fg=self.themes[self.current_theme]['text_color'], font=('Helvetica', 12),
                                               selectbackground='#0a84ff', activestyle='none')
            self.launcher_listbox.pack(fill='both', expand=True, padx=10, pady=(0,10))
            self.launcher_listbox.bind('<<ListboxSelect>>', lambda e: None)
        else:
            self.launcher_listbox.delete(0, 'end')
        for name, cmd in self.launcher_results:
            self.launcher_listbox.insert('end', f"{name}  ({cmd})")
        self.launcher_listbox_index = -1

    def launcher_navigate_down(self, event):
        if self.launcher_listbox:
            if self.launcher_listbox_index < self.launcher_listbox.size() - 1:
                self.launcher_listbox_index += 1
                self.launcher_listbox.selection_clear(0, 'end')
                self.launcher_listbox.selection_set(self.launcher_listbox_index)
                self.launcher_listbox.activate(self.launcher_listbox_index)

    def launcher_navigate_up(self, event):
        if self.launcher_listbox:
            if self.launcher_listbox_index > 0:
                self.launcher_listbox_index -= 1
                self.launcher_listbox.selection_clear(0, 'end')
                self.launcher_listbox.selection_set(self.launcher_listbox_index)
                self.launcher_listbox.activate(self.launcher_listbox_index)

    def launcher_execute(self, event):
        if self.launcher_listbox and self.launcher_listbox_index >= 0:
            _, cmd = self.launcher_results[self.launcher_listbox_index]
        else:
            cmd = self.launcher_entry.get().strip()
        if cmd:
            self.launch_app(cmd)
        self.launcher_win.destroy()

    # --- App Launching ---
    def launch_app(self, app_cmd):
        if app_cmd == 'xterm':
            subprocess.Popen(['xterm'])
        elif app_cmd == 'firefox':
            subprocess.Popen(['firefox'])
        else:
            # Try to run as system command
            try:
                subprocess.Popen(app_cmd, shell=True)
            except Exception as e:
                self.show_notification(f"No s'ha pogut obrir: {app_cmd}")

    # --- FileManager (Finder) ---
    def open_filemanager(self, path=None):
        if path is None:
            path = os.path.expanduser('~')
        win = tk.Toplevel(self.root)
        win.title("Finder")
        win.geometry("800x500+200+100")
        winfo = self.wm.add_window(win, "Finder")
        content = winfo['content']
        self.open_windows.append(win)
        self.active_window = win
        self.update_topbar_title()

        # Address bar
        addr_frame = tk.Frame(content, bg=self.themes[self.current_theme]['bg'])
        addr_frame.pack(fill='x')
        addr_var = tk.StringVar(value=path)
        addr_entry = tk.Entry(addr_frame, textvariable=addr_var, font=('Helvetica', 11), bg=self.themes[self.current_theme]['entry_bg'],
                              fg=self.themes[self.current_theme]['text_color'])
        addr_entry.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        go_btn = tk.Button(addr_frame, text="Obrir", command=lambda: self.fm_navigate(addr_var.get(), tree))
        go_btn.pack(side='right', padx=5)

        # File list
        tree_frame = tk.Frame(content, bg=self.themes[self.current_theme]['bg'])
        tree_frame.pack(fill='both', expand=True)
        tree = ttk.Treeview(tree_frame, columns=('size', 'type'), show='headings')
        tree.heading('#0', text='Nom')
        tree.heading('size', text='Mida')
        tree.heading('type', text='Tipus')
        tree.column('#0', width=300)
        tree.column('size', width=100)
        tree.column('type', width=100)
        tree.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)

        # Bind double-click
        tree.bind('<Double-1>', lambda e: self.fm_open_item(tree, addr_var.get()))
        # Right-click context menu
        tree.bind('<Button-3>', lambda e: self.fm_context_menu(e, tree, addr_var.get()))

        self.fm_populate(tree, path)

        # Keep reference
        win.fm_tree = tree
        win.fm_addr_var = addr_var

        win.bind('<FocusIn>', lambda e: self.set_active_window(win))

    def fm_populate(self, tree, path):
        tree.delete(*tree.get_children())
        try:
            items = os.listdir(path)
            dirs = sorted([d for d in items if os.path.isdir(os.path.join(path, d))])
            files = sorted([f for f in items if not os.path.isdir(os.path.join(path, f))])
            for d in dirs:
                tree.insert('', 'end', text=f"📁 {d}", values=('--', 'Carpeta'))
            for f in files:
                fpath = os.path.join(path, f)
                size = os.path.getsize(fpath) if os.path.isfile(fpath) else '--'
                tree.insert('', 'end', text=f"📄 {f}", values=(self.human_size(size), 'Fitxer'))
        except Exception as e:
            self.show_notification(f"Error en obrir directori: {e}")

    def fm_navigate(self, path, tree):
        if os.path.isdir(path):
            self.fm_populate(tree, path)
            tree.master.master.winfo_toplevel().fm_addr_var.set(path)
        else:
            self.show_notification("No és un directori vàlid")

    def fm_open_item(self, tree, current_path):
        selection = tree.selection()
        if not selection:
            return
        item_text = tree.item(selection[0], 'text')
        # Remove emoji prefix
        name = item_text[2:]
        full_path = os.path.join(current_path, name)
        if os.path.isdir(full_path):
            self.fm_navigate(full_path, tree)
        else:
            # Open with default app
            subprocess.Popen(['xdg-open', full_path])

    def fm_context_menu(self, event, tree, current_path):
        popup = tk.Menu(self.root, tearoff=0)
        popup.add_command(label="Crear carpeta", command=lambda: self.fm_create_folder(tree, current_path))
        selection = tree.selection()
        if selection:
            item = tree.item(selection[0], 'text')[2:]
            full = os.path.join(current_path, item)
            popup.add_command(label="Eliminar", command=lambda: self.fm_delete(full, tree, current_path))
            popup.add_command(label="Renombrar", command=lambda: self.fm_rename(full, tree, current_path))
        try:
            popup.tk_popup(event.x_root, event.y_root)
        finally:
            popup.grab_release()

    def fm_create_folder(self, tree, path):
        name = simpledialog.askstring("Nova carpeta", "Nom:")
        if name:
            os.makedirs(os.path.join(path, name), exist_ok=True)
            self.fm_populate(tree, path)

    def fm_delete(self, path, tree, current_path):
        if messagebox.askyesno("Eliminar", f"Segur que vols eliminar {os.path.basename(path)}?"):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.fm_populate(tree, current_path)

    def fm_rename(self, old_path, tree, current_path):
        new_name = simpledialog.askstring("Renombrar", "Nou nom:")
        if new_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            os.rename(old_path, new_path)
            self.fm_populate(tree, current_path)

    @staticmethod
    def human_size(size):
        for unit in ['B','KB','MB','GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    # --- Settings App ---
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Preferències del Sistema")
        win.geometry("600x400+300+150")
        winfo = self.wm.add_window(win, "Preferències del Sistema")
        content = winfo['content']
        self.open_windows.append(win)
        self.active_window = win
        self.update_topbar_title()

        notebook = ttk.Notebook(content)
        notebook.pack(fill='both', expand=True)

        # General tab
        general = tk.Frame(notebook, bg=self.themes[self.current_theme]['bg'])
        notebook.add(general, text="General")
        tk.Label(general, text="Fons de pantalla:", bg=self.themes[self.current_theme]['bg'],
                 fg=self.themes[self.current_theme]['text_color']).pack(pady=10)
        btn_frame = tk.Frame(general, bg=self.themes[self.current_theme]['bg'])
        btn_frame.pack()
        tk.Button(btn_frame, text="Seleccionar imatge", command=self.select_wallpaper).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Mode: Centrat/Escalat/Mosaic", command=self.cycle_wallpaper_mode).pack(side='left', padx=5)
        self.wallpaper_mode_label = tk.Label(general, text=f"Mode actual: {self.wallpaper_mode}",
                                             bg=self.themes[self.current_theme]['bg'], fg=self.themes[self.current_theme]['text_color'])
        self.wallpaper_mode_label.pack(pady=5)

        # Dock tab
        dock_frame = tk.Frame(notebook, bg=self.themes[self.current_theme]['bg'])
        notebook.add(dock_frame, text="Dock")
        zoom_var = tk.BooleanVar(value=self.dock_zoom_enabled)
        tk.Checkbutton(dock_frame, text="Efecte zoom", variable=zoom_var, command=lambda: self.toggle_dock_zoom(zoom_var.get()),
                       bg=self.themes[self.current_theme]['bg'], fg=self.themes[self.current_theme]['text_color']).pack(anchor='w')
        pos_var = tk.StringVar(value=self.dock_position)
        tk.Label(dock_frame, text="Posició:", bg=self.themes[self.current_theme]['bg'], fg=self.themes[self.current_theme]['text_color']).pack(anchor='w')
        for pos in ['bottom', 'left', 'right']:
            tk.Radiobutton(dock_frame, text=pos, variable=pos_var, value=pos,
                           command=lambda p=pos: self.change_dock_position(p),
                           bg=self.themes[self.current_theme]['bg'], fg=self.themes[self.current_theme]['text_color']).pack(anchor='w')

        # Top Bar tab
        topbar_frame = tk.Frame(notebook, bg=self.themes[self.current_theme]['bg'])
        notebook.add(topbar_frame, text="Top Bar")
        global_menu_var = tk.BooleanVar(value=self.config.get('global_menu', True))
        tk.Checkbutton(topbar_frame, text="Menú global", variable=global_menu_var,
                       command=lambda: self.toggle_global_menu(global_menu_var.get()),
                       bg=self.themes[self.current_theme]['bg'], fg=self.themes[self.current_theme]['text_color']).pack(anchor='w')
        tk.Label(topbar_frame, text="Format hora:", bg=self.themes[self.current_theme]['bg'],
                 fg=self.themes[self.current_theme]['text_color']).pack(anchor='w')
        time_format_var = tk.StringVar(value=self.config.get('time_format', '24h'))
        tk.OptionMenu(topbar_frame, time_format_var, '24h', '12h', command=self.change_time_format).pack(anchor='w')

        # Themes tab
        theme_frame = tk.Frame(notebook, bg=self.themes[self.current_theme]['bg'])
        notebook.add(theme_frame, text="Temes")
        theme_var = tk.StringVar(value=self.current_theme)
        tk.Radiobutton(theme_frame, text="Fosc", variable=theme_var, value='dark',
                       command=lambda: self.change_theme('dark'),
                       bg=self.themes[self.current_theme]['bg'], fg=self.themes[self.current_theme]['text_color']).pack(anchor='w')
        tk.Radiobutton(theme_frame, text="Clar", variable=theme_var, value='light',
                       command=lambda: self.change_theme('light'),
                       bg=self.themes[self.current_theme]['bg'], fg=self.themes[self.current_theme]['text_color']).pack(anchor='w')

        win.bind('<FocusIn>', lambda e: self.set_active_window(win))

    def select_wallpaper(self):
        path = filedialog.askopenfilename(filetypes=[("Imatges", "*.png *.jpg *.jpeg")])
        if path:
            self.set_wallpaper(path)

    def cycle_wallpaper_mode(self):
        modes = ['center', 'scale', 'tile']
        idx = modes.index(self.wallpaper_mode)
        self.wallpaper_mode = modes[(idx + 1) % 3]
        self.config['wallpaper_mode'] = self.wallpaper_mode
        self.save_config()
        self.wallpaper_mode_label.config(text=f"Mode actual: {self.wallpaper_mode}")
        self.set_wallpaper(self.wallpaper_path)

    def toggle_dock_zoom(self, enabled):
        self.dock_zoom_enabled = enabled
        self.config['dock_zoom'] = enabled
        self.save_config()

    def change_dock_position(self, pos):
        self.dock_position = pos
        self.config['dock_position'] = pos
        self.save_config()
        # Reconfigure dock position (simplified: just bottom)
        if pos == 'bottom':
            self.dock.geometry(f"600x70+{(self.screen_width-600)//2}+{self.screen_height-70}")
        else:
            # Left/right not fully implemented
            self.show_notification("Posició esquerra/dreta no implementada")

    def toggle_global_menu(self, enabled):
        self.config['global_menu'] = enabled
        self.save_config()
        if enabled:
            for mb in self.menu_buttons:
                mb.pack(side='left')
        else:
            for mb in self.menu_buttons:
                mb.pack_forget()

    def change_time_format(self, format):
        self.config['time_format'] = format
        self.save_config()
        self.update_clock()

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.config['theme'] = theme_name
        self.save_config()
        self.apply_theme()
        # Update topbar, dock colors
        self.topbar.configure(bg=self.themes[theme_name]['topbar_bg'])
        self.dock.configure(bg=self.themes[theme_name]['dock_bg'])
        self.dock_canvas.configure(bg=self.themes[theme_name]['dock_bg'])
        # Recreate dock icons with new bg? (simplify by updating labels)
        for icon in self.dock_icons:
            icon['label'].configure(bg=self.themes[theme_name]['dock_bg'])
        # Update windows (would need to recursively update all widgets)
        self.show_notification(f"Tema canviat a {theme_name}. Cal reiniciar finestres per efecte complet.")

    # --- Window management helpers ---
    def set_active_window(self, win):
        self.active_window = win
        self.update_topbar_title()
        self.update_global_menus()

    # --- Notifications ---
    def show_notification(self, message, icon=None):
        self.notification_queue.append(message)
        if not self.notification_win or not self.notification_win.winfo_exists():
            self.display_next_notification()

    def display_next_notification(self):
        if not self.notification_queue:
            return
        message = self.notification_queue.pop(0)
        if self.notification_win:
            self.notification_win.destroy()
        self.notification_win = tk.Toplevel(self.root)
        self.notification_win.overrideredirect(True)
        self.notification_win.attributes('-topmost', True)
        self.notification_win.configure(bg='#3d3d3d')
        self.notification_win.geometry(f"300x50+{self.screen_width-310}+30")
        label = tk.Label(self.notification_win, text=message, fg='white', bg='#3d3d3d', font=('Helvetica', 11))
        label.pack(expand=True, fill='both', padx=10)
        # Auto-close after 3 seconds and show next
        self.root.after(3000, self.close_notification_and_next)

    def close_notification_and_next(self):
        if self.notification_win:
            self.notification_win.destroy()
            self.notification_win = None
        self.display_next_notification()

    # --- Shortcuts ---
    def bind_shortcuts(self):
        self.root.bind('<Alt-space>', self.show_launcher)
        self.root.bind('<Alt-Tab>', self.alt_tab)
        # For Alt+Tab to work, we need to capture key events on all toplevels? We'll bind on root.

    def alt_tab(self, event):
        # Cycle through open windows
        if not self.open_windows:
            return
        try:
            current_idx = self.open_windows.index(self.active_window) if self.active_window in self.open_windows else -1
        except ValueError:
            current_idx = -1
        next_idx = (current_idx + 1) % len(self.open_windows)
        next_win = self.open_windows[next_idx]
        next_win.deiconify()
        next_win.lift()
        next_win.focus_set()
        self.active_window = next_win
        self.update_topbar_title()
        self.update_global_menus()

if __name__ == '__main__':
    AlpineDesktop()
