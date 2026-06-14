import tkinter as tk

class WindowManager:
    def __init__(self, desktop):
        self.desktop = desktop
        self.windows = []

    def add_window(self, toplevel, title="Sense títol"):
        theme = self.desktop.theme
        toplevel.overrideredirect(True)
        toplevel.configure(bg=theme['bg'])

        # Marc de decoració
        deco = tk.Frame(toplevel, bg=theme['window_title_bg'], height=28)
        deco.pack(fill='x', side='top')
        deco.pack_propagate(False)

        # Títol
        title_lbl = tk.Label(deco, text=title, fg=theme['window_title_fg'],
                             bg=theme['window_title_bg'], font=('Helvetica', 10, 'bold'))
        title_lbl.pack(side='left', padx=5)

        # Botons
        btn_frame = tk.Frame(deco, bg=theme['window_title_bg'])
        btn_frame.pack(side='right', padx=5)

        tk.Button(btn_frame, text='●', fg=theme['button_close'], bg=theme['window_title_bg'],
                  bd=0, font=('Helvetica', 12, 'bold'),
                  command=lambda: self.close_window(toplevel)).pack(side='left', padx=2)
        tk.Button(btn_frame, text='●', fg=theme['button_minimize'], bg=theme['window_title_bg'],
                  bd=0, font=('Helvetica', 12, 'bold'),
                  command=lambda: self.minimize_window(toplevel)).pack(side='left', padx=2)
        tk.Button(btn_frame, text='●', fg=theme['button_maximize'], bg=theme['window_title_bg'],
                  bd=0, font=('Helvetica', 12, 'bold'),
                  command=lambda: self.maximize_window(toplevel)).pack(side='left', padx=2)

        # Arrossegament
        deco.bind('<Button-1>', lambda e, w=toplevel: self._start_drag(w, e))
        deco.bind('<B1-Motion>', lambda e, w=toplevel: self._do_drag(w, e))
        deco.bind('<Double-Button-1>', lambda e, w=toplevel: self.maximize_window(w))

        # Contingut
        content = tk.Frame(toplevel, bg=theme['bg'])
        content.pack(fill='both', expand=True)

        info = {'toplevel': toplevel, 'title': title, 'title_lbl': title_lbl,
                'deco': deco, 'content': content, 'maximized': False, 'prev_geom': None}
        self.windows.append(info)

        toplevel.bind('<FocusIn>', lambda e, w=toplevel: self.desktop.set_active_window(w))
        toplevel.protocol("WM_DELETE_WINDOW", lambda w=toplevel: self.close_window(w))
        return info

    def _start_drag(self, win, event):
        win._drag_data = {'x': event.x_root, 'y': event.y_root}

    def _do_drag(self, win, event):
        if hasattr(win, '_drag_data'):
            dx = event.x_root - win._drag_data['x']
            dy = event.y_root - win._drag_data['y']
            x = win.winfo_x() + dx
            y = win.winfo_y() + dy
            win.geometry(f'+{x}+{y}')
            win._drag_data = {'x': event.x_root, 'y': event.y_root}

    def close_window(self, win):
        if win in self.desktop.open_windows:
            self.desktop.open_windows.remove(win)
        for w in self.windows:
            if w['toplevel'] == win:
                self.windows.remove(w)
                break
        win.destroy()
        self.desktop.update_active_window()

    def minimize_window(self, win):
        win.withdraw()

    def maximize_window(self, win):
        for w in self.windows:
            if w['toplevel'] == win:
                if not w['maximized']:
                    w['prev_geom'] = win.geometry()
                    top_h = self.desktop.topbar.winfo_height()
                    dock_h = 70
                    win.geometry(f"{self.desktop.screen_width}x{self.desktop.screen_height - top_h - dock_h}+0+{top_h}")
                    w['maximized'] = True
                else:
                    if w['prev_geom']:
                        win.geometry(w['prev_geom'])
                    w['maximized'] = False
                break

    def get_info(self, win):
        for w in self.windows:
            if w['toplevel'] == win:
                return w
        return None
