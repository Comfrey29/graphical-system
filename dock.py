import tkinter as tk
from tkinter import messagebox
import shutil
import os

class Dock:
    def __init__(self, desktop):
        self.desktop = desktop
        self.zoom_enabled = desktop.config.get('dock_zoom', True)
        self.icons = []  # [{emoji, name, command, label, x, open}]
        self.win = tk.Toplevel(desktop.root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg=desktop.theme['dock_bg'])
        dock_w = 600
        self.win.geometry(f"{dock_w}x70+{(desktop.screen_width-dock_w)//2}+{desktop.screen_height-70}")

        self.canvas = tk.Canvas(self.win, bg=desktop.theme['dock_bg'], highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self.canvas.bind('<Motion>', self._motion)
        self.canvas.bind('<Leave>', self._leave)
        self.canvas.bind('<Button-3>', self._right_click_global)

        # Icones per defecte
        self.add_icon('📁', 'Finder', desktop.open_filemanager)
        self.add_icon('▶', 'Terminal', lambda: desktop.launch_app('xterm'))
        self.add_icon('🌐', 'Firefox', lambda: desktop.launch_app('firefox'))
        self.add_icon('⚙️', 'Settings', desktop.open_settings)
        self.add_icon('🗑️', 'Trash', self.empty_trash)

    def add_icon(self, emoji, name, command):
        icon = {'emoji': emoji, 'name': name, 'command': command, 'open': False, 'x': 0}
        lbl = tk.Label(self.canvas, text=emoji, font=('Helvetica', 48),
                       bg=self.desktop.theme['dock_bg'], fg='white', cursor='hand2')
        lbl.bind('<Button-1>', lambda e, i=icon: self._press(i))
        lbl.bind('<Button-3>', lambda e, i=icon: self._right_click_icon(e, i))
        icon['label'] = lbl
        self.icons.append(icon)
        self._arrange()

    def _arrange(self):
        self.canvas.delete('all')
        spacing = 80
        total_w = spacing * len(self.icons)
        canvas_w = self.canvas.winfo_width() or 600
        start_x = (canvas_w - total_w) // 2 + spacing // 2
        for i, icon in enumerate(self.icons):
            x = start_x + i * spacing
            icon['x'] = x
            self.canvas.create_window(x, 35, window=icon['label'], anchor='center')
            if icon['open']:
                self.canvas.create_oval(x-4, 60, x+4, 68, fill='#007aff', outline='')

    def _press(self, icon):
        icon['command']()
        icon['open'] = True
        self._arrange()
        self._bounce(icon)

    def _bounce(self, icon):
        lbl = icon['label']
        original_y = 35
        def bounce(count=0):
            if count >= 6:
                self.canvas.coords(lbl, icon['x'], original_y)
                return
            delta = -10 if count % 2 == 0 else 10
            self.canvas.coords(lbl, icon['x'], original_y + delta)
            self.canvas.after(100, bounce, count+1)
        bounce()

    def _motion(self, event):
        if not self.zoom_enabled:
            return
        for icon in self.icons:
            dist = abs(event.x - icon['x'])
            size = 64 - (dist / 60) * 16 if dist < 60 else 48
            icon['label'].config(font=('Helvetica', int(max(48, min(64, size)))))

    def _leave(self, event):
        for icon in self.icons:
            icon['label'].config(font=('Helvetica', 48))

    def _right_click_icon(self, event, icon):
        popup = tk.Menu(self.desktop.root, tearoff=0)
        popup.add_command(label='Opcions')
        popup.add_command(label='Sortir', command=lambda: self._quit(icon))
        popup.tk_popup(event.x_root, event.y_root)

    def _right_click_global(self, event):
        # Per si es fa clic dret al dock fora d'icona
        pass

    def _quit(self, icon):
        icon['open'] = False
        self._arrange()

    def empty_trash(self):
        trash = os.path.expanduser('~/.local/share/Trash/files')
        if os.path.exists(trash):
            if messagebox.askyesno('Paperera', 'Vols buidar la paperera?'):
                shutil.rmtree(trash)
                os.makedirs(trash, exist_ok=True)
