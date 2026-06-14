import tkinter as tk
import glob
import os
import re

class Launcher:
    def __init__(self, desktop):
        self.desktop = desktop
        self.win = None
        self.results = []
        self.listbox = None
        self.idx = -1

    def show(self, event=None):
        if self.win and self.win.winfo_exists():
            self.win.lift()
            return
        self.win = tk.Toplevel(self.desktop.root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg='#3d3d3d')
        self.win.geometry("500x60+{}+{}".format(
            (self.desktop.screen_width - 500) // 2,
            self.desktop.screen_height // 4))
        self.entry = tk.Entry(self.win, font=('Helvetica', 14), bg='#5a5a5a', fg='white',
                              insertbackground='white', bd=0, relief='flat')
        self.entry.pack(fill='x', padx=10, pady=10)
        self.entry.focus_set()
        self.entry.bind('<KeyRelease>', self.search)
        self.entry.bind('<Down>', self._nav_down)
        self.entry.bind('<Up>', self._nav_up)
        self.entry.bind('<Return>', self._execute)
        self.entry.bind('<Escape>', lambda e: self.win.destroy())

    def search(self, event):
        q = self.entry.get().strip().lower()
        if not q:
            if self.listbox:
                self.listbox.destroy()
                self.listbox = None
            self.win.geometry("500x60")
            return
        self.results = []
        # .desktop
        for df in glob.glob('/usr/share/applications/*.desktop'):
            try:
                with open(df, 'r', encoding='utf-8') as f:
                    content = f.read()
                name_m = re.search(r'^Name=(.*)$', content, re.MULTILINE)
                exec_m = re.search(r'^Exec=(.*)$', content, re.MULTILINE)
                if name_m and exec_m:
                    name = name_m.group(1)
                    cmd = exec_m.group(1).split()[0]
                    if q in name.lower() or q in cmd.lower():
                        self.results.append((name, cmd))
            except:
                pass
        # PATH
        for p in os.environ.get('PATH', '').split(':'):
            if os.path.isdir(p):
                try:
                    for f in os.listdir(p):
                        full = os.path.join(p, f)
                        if os.access(full, os.X_OK) and q in f.lower():
                            self.results.append((f, full))
                except:
                    pass
        # Deduplicar
        seen = set()
        unique = []
        for name, cmd in self.results:
            if (name, cmd) not in seen:
                seen.add((name, cmd))
                unique.append((name, cmd))
        self.results = unique[:10]

        if not self.listbox:
            self.win.geometry("500x300")
            self.listbox = tk.Listbox(self.win, bg='#2d2d2d', fg='white', font=('Helvetica', 12),
                                      selectbackground='#0a84ff', activestyle='none')
            self.listbox.pack(fill='both', expand=True, padx=10, pady=(0,10))
        else:
            self.listbox.delete(0, 'end')
        for name, cmd in self.results:
            self.listbox.insert('end', f"{name}  ({cmd})")
        self.idx = -1

    def _nav_down(self, event):
        if self.listbox and self.listbox.size() > 0:
            self.idx = min(self.idx + 1, self.listbox.size() - 1)
            self.listbox.selection_clear(0, 'end')
            self.listbox.selection_set(self.idx)
            self.listbox.activate(self.idx)

    def _nav_up(self, event):
        if self.listbox and self.listbox.size() > 0:
            self.idx = max(self.idx - 1, 0)
            self.listbox.selection_clear(0, 'end')
            self.listbox.selection_set(self.idx)
            self.listbox.activate(self.idx)

    def _execute(self, event):
        if self.listbox and self.idx >= 0:
            _, cmd = self.results[self.idx]
        else:
            cmd = self.entry.get().strip()
        if cmd:
            self.desktop.launch_app(cmd)
        self.win.destroy()
