import tkinter as tk
from tkinter import messagebox
import time

class TopBar:
    def __init__(self, desktop):
        self.desktop = desktop
        self.win = tk.Toplevel(desktop.root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg=desktop.theme['topbar_bg'])
        self.win.geometry(f"{desktop.screen_width}x28+0+0")

        # Logotip Apple
        apple = tk.Label(self.win, text='', fg='white', bg=desktop.theme['topbar_bg'],
                         font=('Helvetica', 12, 'bold'), cursor='hand2')
        apple.pack(side='left', padx=5)
        apple.bind('<Button-1>', self.show_apple_menu)

        # Títol app
        self.title_lbl = tk.Label(self.win, text='Finder', fg='white',
                                  bg=desktop.theme['topbar_bg'], font=('Helvetica', 10))
        self.title_lbl.pack(side='left', expand=True)

        # Menús globals
        self.menu_frame = tk.Frame(self.win, bg=desktop.theme['topbar_bg'])
        self.menu_frame.pack(side='left', padx=10)
        self.menus = []
        for m in ['Fitxer', 'Edita', 'Visualitza']:
            mb = tk.Menubutton(self.menu_frame, text=m, fg='white', bg=desktop.theme['topbar_bg'],
                               activebackground='#505050', font=('Helvetica', 10), bd=0, padx=5)
            mb.menu = tk.Menu(mb, tearoff=0)
            mb['menu'] = mb.menu
            mb.pack(side='left')
            self.menus.append(mb)

        # Hora, bateria, xarxa
        right = tk.Frame(self.win, bg=desktop.theme['topbar_bg'])
        right.pack(side='right', padx=10)
        self.clock_lbl = tk.Label(right, text='', fg='white', bg=desktop.theme['topbar_bg'], font=('Helvetica', 9))
        self.clock_lbl.pack(side='left', padx=5)
        self.battery_lbl = tk.Label(right, text='🔋 ---%', fg='white', bg=desktop.theme['topbar_bg'], font=('Helvetica', 9))
        self.battery_lbl.pack(side='left', padx=5)
        tk.Label(right, text='📶', fg='white', bg=desktop.theme['topbar_bg'], font=('Helvetica', 9)).pack(side='left', padx=5)

        self.update_clock()

    def show_apple_menu(self, event):
        popup = tk.Menu(self.desktop.root, tearoff=0)
        popup.add_command(label='Quant a aquest Mac', command=lambda: messagebox.showinfo('Quant a', 'Alpine Desktop 1.0'))
        popup.add_command(label='Preferències del Sistema', command=self.desktop.open_settings)
        popup.add_separator()
        popup.add_command(label='Bloquejar pantalla', command=self.desktop.lock_screen)
        popup.add_command(label='Reiniciar sessió', command=self.desktop.restart_session)
        popup.add_command(label='Apagar', command=self.desktop.shutdown)
        popup.tk_popup(event.x_root, event.y_root)

    def update_clock(self):
        now = time.localtime()
        days = ['dll.', 'dma.', 'dmc.', 'dij.', 'div.', 'dss.', 'dmg.']
        day = days[now.tm_wday]
        date_str = f"{day} {now.tm_mday}/{now.tm_mon}"
        time_str = f"{now.tm_hour:02d}:{now.tm_min:02d}"
        self.clock_lbl.config(text=f"{date_str} {time_str}")
        self.desktop.root.after(30000, self.update_clock)

    def set_title(self, title):
        self.title_lbl.config(text=title)

    def update_global_menus(self, window_info):
        for mb in self.menus:
            mb.menu.delete(0, 'end')
        if window_info:
            # Fitxer
            self.menus[0].menu.add_command(label='Tancar finestra', command=lambda: self.desktop.wm.close_window(window_info['toplevel']))
            self.menus[0].menu.add_command(label='Sortir', command=self.desktop.root.destroy)
            # Edita (placeholder)
            self.menus[1].menu.add_command(label='Desfer')
            self.menus[1].menu.add_command(label='Refer')
            # Visualitza
            self.menus[2].menu.add_command(label='Maximitzar', command=lambda: self.desktop.wm.maximize_window(window_info['toplevel']))
