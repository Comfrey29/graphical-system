#!/usr/bin/env python3
"""
Escriptori estil macOS amb Tkinter
Combina: Dock, Top Bar, Launcher i Notificacions
"""

import tkinter as tk
from tkinter import font, messagebox
import subprocess
import os
from datetime import datetime
import threading
import time

class MacDesktop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Alpine Desktop")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#1e1e2e')
        
        # Variables
        self.notification_windows = []
        
        # Configuració de colors (estil macOS)
        self.colors = {
            'bg_dark': '#2c2c2e',
            'bg_dock': '#4c4c4e',
            'text': '#ffffff',
            'highlight': '#0a84ff',
            'close': '#ff5f56',
            'minimize': '#ffbd2e',
            'maximize': '#27c93f'
        }
        
        # Apps del dock
        self.dock_apps = [
            {"name": "Terminal", "cmd": "xterm", "icon": "▶"},
            {"name": "Firefox", "cmd": "firefox", "icon": "🌐"},
            {"name": "Files", "cmd": "thunar", "icon": "📁"},
            {"name": "Editor", "cmd": "vim", "icon": "{"}
        ]
        
        self.setup_ui()
        self.update_clock()
        self.root.mainloop()
    
    def setup_ui(self):
        """Configura tota la interfície"""
        # --- TOP BAR (estil macOS) ---
        self.top_bar = tk.Frame(
            self.root, bg=self.colors['bg_dark'], 
            height=28, relief='flat'
        )
        self.top_bar.pack(fill='x', side='top')
        self.top_bar.pack_propagate(False)
        
        # Logo Apple (esquerra)
        self.apple_menu = tk.Menubutton(
            self.top_bar, text="", font=('Helvetica', 14),
            bg=self.colors['bg_dark'], fg=self.colors['text'],
            activebackground=self.colors['highlight'], relief='flat'
        )
        self.apple_menu.pack(side='left', padx=15)
        
        # Menú Apple
        apple_menu = tk.Menu(self.apple_menu, tearoff=0, bg=self.colors['bg_dark'], fg=self.colors['text'])
        apple_menu.add_command(label="About This Mac", command=self.show_about)
        apple_menu.add_separator()
        apple_menu.add_command(label="Lock Screen", command=self.lock_screen)
        apple_menu.add_command(label="Logout", command=self.logout)
        apple_menu.add_command(label="Shutdown", command=self.shutdown)
        self.apple_menu.config(menu=apple_menu)
        
        # Títol de l'app activa (centre)
        self.title_label = tk.Label(
            self.top_bar, text="Desktop", font=('Helvetica', 12, 'bold'),
            bg=self.colors['bg_dark'], fg=self.colors['text']
        )
        self.title_label.pack(side='left', expand=True)
        
        # Widgets de la dreta (hora, bateria)
        self.clock_label = tk.Label(
            self.top_bar, font=('Helvetica', 11),
            bg=self.colors['bg_dark'], fg=self.colors['text']
        )
        self.clock_label.pack(side='right', padx=15)
        
        self.battery_label = tk.Label(
            self.top_bar, text="🔋 100%", font=('Helvetica', 10),
            bg=self.colors['bg_dark'], fg=self.colors['text']
        )
        self.battery_label.pack(side='right', padx=10)
        
        # --- DOCK (estil macOS) ---
        self.dock_frame = tk.Frame(
            self.root, bg=self.colors['bg_dock'], 
            height=70, relief='flat', bd=0
        )
        
        # Centrar el dock
        self.dock_frame.place(relx=0.5, rely=1.0, y=-10, anchor='s')
        self.dock_frame.pack_propagate(False)
        
        # Icones del dock
        self.dock_icons = []
        for i, app in enumerate(self.dock_apps):
            icon_frame = tk.Frame(
                self.dock_frame, bg=self.colors['bg_dock'],
                width=60, height=60, cursor="hand2"
            )
            icon_frame.pack(side='left', padx=5, pady=5)
            icon_frame.pack_propagate(False)
            
            # Efecte hover
            icon_frame.bind("<Enter>", lambda e, f=icon_frame: self.dock_hover_enter(f))
            icon_frame.bind("<Leave>", lambda e, f=icon_frame: self.dock_hover_leave(f))
            icon_frame.bind("<Button-1>", lambda e, cmd=app['cmd']: self.launch_app(cmd))
            
            # Icona (text per ara, després pots posar imatges)
            icon_label = tk.Label(
                icon_frame, text=app['icon'], font=('Segoe UI Emoji', 28),
                bg=self.colors['bg_dock'], fg=self.colors['text']
            )
            icon_label.pack(expand=True)
            
            # Nom de l'app
            name_label = tk.Label(
                icon_frame, text=app['name'], font=('Helvetica', 8),
                bg=self.colors['bg_dock'], fg=self.colors['text']
            )
            name_label.pack()
            
            self.dock_icons.append(icon_frame)
        
        # Indicador d'apps obertes (punt blau)
        for icon in self.dock_icons:
            indicator = tk.Label(
                icon, text="●", font=('Helvetica', 8),
                bg=self.colors['bg_dock'], fg=self.colors['highlight']
            )
            indicator.place(relx=0.5, rely=1.0, y=-5, anchor='s')
        
        # --- LAUNCHER (amagat inicialment) ---
        self.launcher_frame = tk.Frame(
            self.root, bg='#2c2c2e', bd=1, relief='solid'
        )
        self.launcher_entry = tk.Entry(
            self.launcher_frame, font=('Helvetica', 14),
            bg='#3a3a3c', fg='white', insertbackground='white',
            relief='flat', width=40
        )
        self.launcher_entry.pack(padx=10, pady=10)
        self.launcher_entry.bind('<Return>', self.launcher_execute)
        self.launcher_entry.bind('<Escape>', lambda e: self.hide_launcher())
        
        self.launcher_results = tk.Listbox(
            self.launcher_frame, font=('Helvetica', 11),
            bg='#2c2c2e', fg='white', selectbackground=self.colors['highlight'],
            height=8, relief='flat'
        )
        self.launcher_results.pack(fill='both', expand=True, padx=10, pady=(0,10))
        self.launcher_results.bind('<Button-1>', self.launcher_select)
        
        self.hide_launcher()
        
        # Bind tecla per obrir launcher (Alt+Espai)
        self.root.bind('<Alt-space>', lambda e: self.show_launcher())
        self.root.bind('<Alt-plus>', lambda e: self.show_launcher())
    
    def update_clock(self):
        """Actualitza el rellotge cada segon"""
        now = datetime.now()
        self.clock_label.config(text=now.strftime("%H:%M"))
        self.root.after(1000, self.update_clock)
    
    def dock_hover_enter(self, widget):
        """Efecte zoom al dock"""
        widget.config(width=70, height=70)
        widget.place_configure(y=-5)
    
    def dock_hover_leave(self, widget):
        """Reverteix l'efecte zoom"""
        widget.config(width=60, height=60)
        widget.place_configure(y=0)
    
    def launch_app(self, command):
        """Executa una aplicació"""
        try:
            subprocess.Popen(command, shell=True)
            self.show_notification(f"Obrint {command}")
        except Exception as e:
            self.show_notification(f"Error: {e}")
    
    def show_notification(self, message, duration=3):
        """Mostra una notificació estil macOS"""
        notif = tk.Toplevel(self.root)
        notif.overrideredirect(True)
        notif.configure(bg=self.colors['bg_dark'])
        notif.geometry(f"300x60+{self.root.winfo_screenwidth()-320}+40")
        
        tk.Label(
            notif, text="🔔", font=('Segoe UI Emoji', 16),
            bg=self.colors['bg_dark'], fg=self.colors['highlight']
        ).pack(side='left', padx=10)
        
        tk.Label(
            notif, text=message, font=('Helvetica', 11),
            bg=self.colors['bg_dark'], fg=self.colors['text']
        ).pack(side='left', padx=5)
        
        # Auto-destrucció
        self.notification_windows.append(notif)
        notif.after(duration * 1000, lambda: self.destroy_notification(notif))
    
    def destroy_notification(self, notif):
        notif.destroy()
        if notif in self.notification_windows:
            self.notification_windows.remove(notif)
    
    def show_launcher(self):
        """Mostra el launcher (estil Spotlight)"""
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 300) // 3
        self.launcher_frame.place(x=x, y=y, width=500, height=300)
        self.launcher_entry.delete(0, tk.END)
        self.launcher_entry.focus()
        self.update_launcher_results()
    
    def hide_launcher(self):
        self.launcher_frame.place_forget()
    
    def update_launcher_results(self, event=None):
        """Actualitza els resultats de cerca"""
        search = self.launcher_entry.get().lower()
        self.launcher_results.delete(0, tk.END)
        
        # Apps per defecte
        apps = [
            ("Terminal", "xterm"), ("Firefox", "firefox"),
            ("Files", "thunar"), ("Editor", "vim"),
            ("Calculator", "bc -l"), ("Logout", "logout")
        ]
        
        for name, cmd in apps:
            if search in name.lower():
                self.launcher_results.insert(tk.END, f"{name}  →  {cmd}")
        
        self.launcher_entry.bind('<KeyRelease>', self.update_launcher_results)
    
    def launcher_execute(self, event):
        """Executa l'app seleccionada"""
        selection = self.launcher_results.curselection()
        if selection:
            text = self.launcher_results.get(selection[0])
            cmd = text.split("→")[-1].strip()
            if cmd == "logout":
                self.logout()
            else:
                self.launch_app(cmd)
        self.hide_launcher()
    
    def launcher_select(self, event):
        self.launcher_execute(None)
    
    def show_about(self):
        messagebox.showinfo("About", "Alpine Desktop Environment\nEstil macOS\nVersió 1.0")
    
    def lock_screen(self):
        self.show_notification("Pantalla bloquejada (simulat)")
    
    def logout(self):
        if messagebox.askyesno("Logout", "Vols tancar la sessió?"):
            self.root.quit()
            os.system("pkill Xorg")
    
    def shutdown(self):
        if messagebox.askyesno("Shutdown", "Vols apagar el sistema?"):
            os.system("poweroff")

if __name__ == "__main__":
    MacDesktop()
