import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import shutil
import subprocess
from utils import human_size

class FileManager:
    def __init__(self, desktop, path=None):
        self.desktop = desktop
        if path is None:
            path = os.path.expanduser('~')
        self.win = tk.Toplevel(desktop.root)
        self.win.geometry("800x500+200+100")
        winfo = desktop.wm.add_window(self.win, "Finder")
        self.content = winfo['content']
        self.current_path = path

        # Barra d'adreces
        addr_frame = tk.Frame(self.content, bg=desktop.theme['bg'])
        addr_frame.pack(fill='x')
        self.addr_var = tk.StringVar(value=path)
        tk.Entry(addr_frame, textvariable=self.addr_var, font=('Helvetica', 11),
                 bg=desktop.theme['entry_bg'], fg=desktop.theme['text_color']).pack(side='left', fill='x', expand=True, padx=5, pady=5)
        tk.Button(addr_frame, text='Obrir', command=self._navigate).pack(side='right', padx=5)

        # Arbre de fitxers
        tree_frame = tk.Frame(self.content, bg=desktop.theme['bg'])
        tree_frame.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=('size', 'type'), show='headings')
        self.tree.heading('#0', text='Nom')
        self.tree.heading('size', text='Mida')
        self.tree.heading('type', text='Tipus')
        self.tree.column('#0', width=300)
        self.tree.column('size', width=100)
        self.tree.column('type', width=100)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        scroll.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind('<Double-1>', self._open_item)
        self.tree.bind('<Button-3>', self._context_menu)

        self._populate()
        self.win.bind('<FocusIn>', lambda e: self.desktop.set_active_window(self.win))

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        try:
            items = os.listdir(self.current_path)
            dirs = sorted([d for d in items if os.path.isdir(os.path.join(self.current_path, d))])
            files = sorted([f for f in items if not os.path.isdir(os.path.join(self.current_path, f))])
            for d in dirs:
                self.tree.insert('', 'end', text=f'📁 {d}', values=('--', 'Carpeta'))
            for f in files:
                full = os.path.join(self.current_path, f)
                size = os.path.getsize(full) if os.path.isfile(full) else '--'
                self.tree.insert('', 'end', text=f'📄 {f}', values=(human_size(size), 'Fitxer'))
        except Exception as e:
            self.desktop.show_notification(f"Error: {e}")

    def _navigate(self, path=None):
        if path is None:
            path = self.addr_var.get()
        if os.path.isdir(path):
            self.current_path = path
            self.addr_var.set(path)
            self._populate()

    def _open_item(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0], 'text')[2:]  # treure emoji
        full = os.path.join(self.current_path, name)
        if os.path.isdir(full):
            self._navigate(full)
        else:
            subprocess.Popen(['xdg-open', full])

    def _context_menu(self, event):
        popup = tk.Menu(self.desktop.root, tearoff=0)
        popup.add_command(label='Crear carpeta', command=self._create_folder)
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0], 'text')[2:]
            full = os.path.join(self.current_path, item)
            popup.add_command(label='Eliminar', command=lambda: self._delete(full))
            popup.add_command(label='Renombrar', command=lambda: self._rename(full))
        popup.tk_popup(event.x_root, event.y_root)

    def _create_folder(self):
        name = simpledialog.askstring('Nova carpeta', 'Nom:')
        if name:
            os.makedirs(os.path.join(self.current_path, name), exist_ok=True)
            self._populate()

    def _delete(self, path):
        if messagebox.askyesno('Eliminar', f'Segur que vols eliminar {os.path.basename(path)}?'):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self._populate()

    def _rename(self, old):
        new = simpledialog.askstring('Renombrar', 'Nou nom:')
        if new:
            new_path = os.path.join(os.path.dirname(old), new)
            os.rename(old, new_path)
            self._populate()
