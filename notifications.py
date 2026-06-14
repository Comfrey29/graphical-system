import tkinter as tk

class Notifications:
    def __init__(self, desktop):
        self.desktop = desktop
        self.queue = []
        self.current = None

    def show(self, message):
        self.queue.append(message)
        if not self.current:
            self._display_next()

    def _display_next(self):
        if not self.queue:
            return
        msg = self.queue.pop(0)
        self.current = tk.Toplevel(self.desktop.root)
        self.current.overrideredirect(True)
        self.current.attributes('-topmost', True)
        self.current.configure(bg='#3d3d3d')
        self.current.geometry(f"300x50+{self.desktop.screen_width - 310}+30")
        tk.Label(self.current, text=msg, fg='white', bg='#3d3d3d', font=('Helvetica', 11)).pack(expand=True, fill='both', padx=10)
        self.desktop.root.after(3000, self._close_and_next)

    def _close_and_next(self):
        if self.current:
            self.current.destroy()
            self.current = None
        self._display_next()
