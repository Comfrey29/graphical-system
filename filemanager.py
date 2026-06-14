# -*- coding: utf-8 -*-
"""
FileManager (Finder) per Alpine Desktop.
S'adapta a la mida de la pantalla i a la barra superior / dock.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import shutil
import subprocess

# Importem la funció auxiliar del mòdul utils
from utils import human_size

class FileManager:
    def __init__(self, desktop, path=None):
        """
        Inicialitza el gestor de fitxers.
        :param desktop: instància d'AlpineDesktop
        :param path: directori inicial (per defecte, home de l'usuari)
        """
        self.desktop = desktop
        if path is None:
            path = os.path.expanduser('~')
        self.current_path = path

        # Dimensions i posició adaptables
        topbar_h = desktop.topbar.win.winfo_height() if desktop.topbar else 28
        dock_h = 70  # alçada estimada del dock
        # Fem servir un 80% de l'amplada i un 75% de l'alçada disponible
        win_w = int(desktop.screen_width * 0.8)
        win_h = int(desktop.screen_height * 0.75)
        # Centrat horitzontalment, sota la barra superior
        win_x = (desktop.screen_width - win_w) // 2
        win_y = topbar_h + int((desktop.screen_height - topbar_h - dock_h - win_h) / 2)

        self.win = tk.Toplevel(desktop.root)
        self.win.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")

        # Afegim la decoració de finestra estil macOS
        winfo = desktop.wm.add_window(self.win, "Finder")
        self.content = winfo['content']  # frame on anirà el contingut

        # ---- Barra d'adreces ----
        addr_frame = tk.Frame(self.content, bg=desktop.theme['bg'])
        addr_frame.pack(fill='x', padx=5, pady=5)

        self.addr_var = tk.StringVar(value=path)
        entry = tk.Entry(
            addr_frame,
            textvariable=self.addr_var,
            font=('Helvetica', 11),
            bg=desktop.theme['entry_bg'],
            fg=desktop.theme['text_color'],
            relief='flat',
            bd=2
        )
        entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        entry.bind('<Return>', lambda e: self._navigate(self.addr_var.get()))

        go_btn = tk.Button(
            addr_frame,
            text='Obrir',
            command=lambda: self._navigate(self.addr_var.get()),
            bg=desktop.theme['window_title_bg'],
            fg=desktop.theme['text_color'],
            bd=1
        )
        go_btn.pack(side='right')

        # ---- Vista de fitxers (Treeview) ----
        tree_frame = tk.Frame(self.content, bg=desktop.theme['bg'])
        tree_frame.pack(fill='both', expand=True, padx=5, pady=(0, 5))

        # Estil del Treeview per respectar el tema
        style = ttk.Style()
        style.configure("Treeview",
                        background=desktop.theme['listbox_bg'],
                        foreground=desktop.theme['text_color'],
                        fieldbackground=desktop.theme['listbox_bg'])
        style.map("Treeview", background=[('selected', '#0a84ff')])

        self.tree = ttk.Treeview(
            tree_frame,
            columns=('size', 'type'),
            show='headings',
            selectmode='browse'
        )
        self.tree.heading('#0', text='Nom')
        self.tree.heading('size', text='Mida')
        self.tree.heading('type', text='Tipus')
        self.tree.column('#0', width=300, stretch=True)
        self.tree.column('size', width=100, anchor='center')
        self.tree.column('type', width=100, anchor='center')

        # Barra de desplaçament
        scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

        # Esdeveniments
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Return>', self._on_double_click)  # tecla Enter
        self.tree.bind('<Button-3>', self._show_context_menu)  # clic dret

        # Emplenar amb el contingut del directori
        self._populate()

        # Focus → actualitza finestra activa
        self.win.bind('<FocusIn>', lambda e: desktop.set_active_window(self.win))

    # --------------------------------------------------
    #  Navegació i ompliment
    # --------------------------------------------------
    def _populate(self):
        """Omple el Treeview amb fitxers i carpetes del directori actual."""
        self.tree.delete(*self.tree.get_children())
        try:
            items = os.listdir(self.current_path)
            # Separar i ordenar
            dirs = sorted([d for d in items if os.path.isdir(os.path.join(self.current_path, d))])
            files = sorted([f for f in items if not os.path.isdir(os.path.join(self.current_path, f))])

            for d in dirs:
                self.tree.insert('', 'end', text=f'📁 {d}', values=('—', 'Carpeta'))
            for f in files:
                full = os.path.join(self.current_path, f)
                size = os.path.getsize(full) if os.path.isfile(full) else 0
                self.tree.insert('', 'end', text=f'📄 {f}',
                                 values=(human_size(size), 'Fitxer'))
        except PermissionError:
            self.desktop.show_notification("Permís denegat")
        except Exception as e:
            self.desktop.show_notification(f"Error: {e}")

    def _navigate(self, dest_path):
        """Canvia al directori destí si és vàlid."""
        if os.path.isdir(dest_path):
            self.current_path = dest_path
            self.addr_var.set(dest_path)
            self._populate()
        else:
            messagebox.showwarning("Error", f"'{dest_path}' no és un directori vàlid.")

    # --------------------------------------------------
    #  Accions amb fitxers i carpetes
    # --------------------------------------------------
    def _get_selected_path(self):
        """Retorna la ruta completa de l'element seleccionat, o None."""
        sel = self.tree.selection()
        if not sel:
            return None
        text = self.tree.item(sel[0], 'text')[2:]  # treu l'emoji i espai
        return os.path.join(self.current_path, text)

    def _on_double_click(self, event):
        """Obre la carpeta o el fitxer amb l'aplicació predeterminada."""
        path = self._get_selected_path()
        if path is None:
            return
        if os.path.isdir(path):
            self._navigate(path)
        else:
            try:
                subprocess.Popen(['xdg-open', path])
            except Exception as e:
                self.desktop.show_notification(f"No s'ha pogut obrir: {e}")

    def _show_context_menu(self, event):
        """Menú contextual del clic dret."""
        popup = tk.Menu(self.desktop.root, tearoff=0)
        popup.add_command(label='Carpeta nova', command=self._create_folder)

        selected = self._get_selected_path()
        if selected:
            popup.add_separator()
            popup.add_command(label='Reanomena', command=lambda: self._rename_item(selected))
            popup.add_command(label='Elimina', command=lambda: self._delete_item(selected))

        popup.tk_popup(event.x_root, event.y_root)

    def _create_folder(self):
        """Crea una carpeta nova al directori actual."""
        name = simpledialog.askstring('Carpeta nova', 'Nom de la carpeta:')
        if name:
            new_path = os.path.join(self.current_path, name)
            try:
                os.makedirs(new_path, exist_ok=False)
                self._populate()
            except FileExistsError:
                messagebox.showwarning("Error", "Ja existeix una carpeta amb aquest nom.")
            except Exception as e:
                self.desktop.show_notification(f"Error en crear carpeta: {e}")

    def _rename_item(self, old_path):
        """Reanomena un fitxer o carpeta."""
        old_name = os.path.basename(old_path)
        new_name = simpledialog.askstring('Reanomena', f'Nou nom per a "{old_name}":')
        if new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self._populate()
            except Exception as e:
                self.desktop.show_notification(f"No s'ha pogut reanomenar: {e}")

    def _delete_item(self, path):
        """Elimina un fitxer o carpeta amb confirmació."""
        name = os.path.basename(path)
        if messagebox.askyesno('Elimina', f"Segur que vols eliminar '{name}'?"):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self._populate()
            except Exception as e:
                self.desktop.show_notification(f"No s'ha pogut eliminar: {e}")
