import os
import json

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.expanduser('~/.config/alpine-de')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, 'config.json')
        self.data = self.load()

    def load(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

class Themes:
    themes = {
        'dark': {
            'topbar_bg': '#2c2c2e', 'dock_bg': '#4c4c4e',
            'window_title_bg': '#3c3c3e', 'window_title_fg': '#ffffff',
            'button_close': '#ff5f57', 'button_minimize': '#febc2e',
            'button_maximize': '#28c840', 'text_color': '#ffffff',
            'bg': '#1e1e1e', 'listbox_bg': '#2d2d2d', 'entry_bg': '#3d3d3d',
            'notebook_bg': '#2c2c2e', 'tab_bg': '#3c3c3e', 'active_tab_bg': '#505050'
        },
        'light': {
            'topbar_bg': '#e0e0e0', 'dock_bg': '#d0d0d0',
            'window_title_bg': '#f0f0f0', 'window_title_fg': '#000000',
            'button_close': '#ff5f57', 'button_minimize': '#febc2e',
            'button_maximize': '#28c840', 'text_color': '#000000',
            'bg': '#ffffff', 'listbox_bg': '#f0f0f0', 'entry_bg': '#ffffff',
            'notebook_bg': '#e0e0e0', 'tab_bg': '#f0f0f0', 'active_tab_bg': '#d0d0d0'
        }
    }

    @classmethod
    def get(cls, theme_name):
        return cls.themes.get(theme_name, cls.themes['dark'])

def human_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
