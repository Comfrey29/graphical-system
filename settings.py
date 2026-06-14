import tkinter as tk
from tkinter import ttk, filedialog

class SettingsApp:
    def __init__(self, desktop):
        self.desktop = desktop
        self.win = tk.Toplevel(desktop.root)
        self.win.geometry("600x400+300+150")
        winfo = desktop.wm.add_window(self.win, "Preferències del Sistema")
        self.content = winfo['content']

        nb = ttk.Notebook(self.content)
        nb.pack(fill='both', expand=True)

        # General
        gen = tk.Frame(nb, bg=desktop.theme['bg'])
        nb.add(gen, text='General')
        tk.Label(gen, text='Fons de pantalla:', bg=desktop.theme['bg'], fg=desktop.theme['text_color']).pack(pady=10)
        btn_fr = tk.Frame(gen, bg=desktop.theme['bg'])
        btn_fr.pack()
        tk.Button(btn_fr, text='Seleccionar imatge', command=self._sel_wallpaper).pack(side='left', padx=5)
        tk.Button(btn_fr, text='Canviar mode', command=self._cycle_mode).pack(side='left', padx=5)
        self.mode_lbl = tk.Label(gen, text=f"Mode: {desktop.wallpaper_mode}", bg=desktop.theme['bg'], fg=desktop.theme['text_color'])
        self.mode_lbl.pack(pady=5)

        # Dock
        dock = tk.Frame(nb, bg=desktop.theme['bg'])
        nb.add(dock, text='Dock')
        self.zoom_var = tk.BooleanVar(value=desktop.dock.zoom_enabled)
        tk.Checkbutton(dock, text='Efecte zoom', variable=self.zoom_var, command=self._toggle_zoom,
                       bg=desktop.theme['bg'], fg=desktop.theme['text_color']).pack(anchor='w')
        pos_var = tk.StringVar(value=desktop.config.get('dock_position', 'bottom'))
        tk.Label(dock, text='Posició:', bg=desktop.theme['bg'], fg=desktop.theme['text_color']).pack(anchor='w')
        for p in ['bottom']:  # només implementat bottom
            tk.Radiobutton(dock, text=p, variable=pos_var, value=p,
                           command=lambda p=p: self._change_pos(p),
                           bg=desktop.theme['bg'], fg=desktop.theme['text_color']).pack(anchor='w')

        # Top Bar
        tb = tk.Frame(nb, bg=desktop.theme['bg'])
        nb.add(tb, text='Top Bar')
        self.menu_var = tk.BooleanVar(value=desktop.config.get('global_menu', True))
        tk.Checkbutton(tb, text='Menú global', variable=self.menu_var, command=self._toggle_menu,
                       bg=desktop.theme['bg'], fg=desktop.theme['text_color']).pack(anchor='w')
        tk.Label(tb, text='Format hora:', bg=desktop.theme['bg'], fg=desktop.theme['text_color']).pack(anchor='w')
        fmt_var = tk.StringVar(value=desktop.config.get('time_format', '24h'))
        tk.OptionMenu(tb, fmt_var, '24h', '12h', command=self._change_fmt).pack(anchor='w')

        # Temes
        th = tk.Frame(nb, bg=desktop.theme['bg'])
        nb.add(th, text='Temes')
        self.theme_var = tk.StringVar(value=desktop.current_theme)
        tk.Radiobutton(th, text='Fosc', variable=self.theme_var, value='dark',
                       command=lambda: self._change_theme('dark'),
                       bg=desktop.theme['bg'], fg=desktop.theme['text_color']).pack(anchor='w')
        tk.Radiobutton(th, text='Clar', variable=self.theme_var, value='light',
                       command=lambda: self._change_theme('light'),
                       bg=desktop.theme['bg'], fg=desktop.theme['text_color']).pack(anchor='w')

        self.win.bind('<FocusIn>', lambda e: desktop.set_active_window(self.win))

    def _sel_wallpaper(self):
        path = filedialog.askopenfilename(filetypes=[('Imatges', '*.png *.jpg *.jpeg')])
        if path:
            self.desktop.set_wallpaper(path)

    def _cycle_mode(self):
        modes = ['center', 'scale', 'tile']
        cur = self.desktop.wallpaper_mode
        idx = modes.index(cur)
        new = modes[(idx + 1) % 3]
        self.desktop.wallpaper_mode = new
        self.desktop.config.set('wallpaper_mode', new)
        self.mode_lbl.config(text=f"Mode: {new}")
        self.desktop.set_wallpaper(self.desktop.wallpaper_path)

    def _toggle_zoom(self):
        val = self.zoom_var.get()
        self.desktop.dock.zoom_enabled = val
        self.desktop.config.set('dock_zoom', val)

    def _change_pos(self, pos):
        self.desktop.config.set('dock_position', pos)
        # No s'implementa canvi de posició real

    def _toggle_menu(self):
        val = self.menu_var.get()
        self.desktop.config.set('global_menu', val)
        if val:
            for mb in self.desktop.topbar.menus:
                mb.pack(side='left')
        else:
            for mb in self.desktop.topbar.menus:
                mb.pack_forget()

    def _change_fmt(self, fmt):
        self.desktop.config.set('time_format', fmt)

    def _change_theme(self, theme):
        self.desktop.current_theme = theme
        self.desktop.theme = self.desktop.themes.get(theme)
        self.desktop.config.set('theme', theme)
        # Actualitzar colors de manera bàsica
        self.desktop.topbar.win.configure(bg=self.desktop.theme['topbar_bg'])
        self.desktop.dock.win.configure(bg=self.desktop.theme['dock_bg'])
        self.desktop.dock.canvas.configure(bg=self.desktop.theme['dock_bg'])
        self.desktop.show_notification(f"Tema canviat a {theme}. Reinicia finestres per efecte complet.")
