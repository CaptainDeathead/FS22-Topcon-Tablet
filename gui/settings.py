import tkinter as tk
import sv_ttk
import json

from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from copy import deepcopy

from ui import UIManager

class Settings:
    DEFAULTS = {
        "log_path": f"{Path.home()}/Documents/My Games/FarmingSimulator2022/",
        "server_port": 5001,
        "working_width_override": 6,
        "enable_working_width_override": False,
        "allow_autosteer": True,

        "ip_client": "",
        "port_client": 5001
    }

    def __init__(self, save_data: dict = None) -> None:
        self.root = tk.Tk()
        self.root.title("Settings")
        self.root.geometry("400x600")

        self.ui_mgr = UIManager(self.root)

        self.log_path = None
        self.get_server_port = lambda: None
        self.get_working_width_override = lambda: None
        self.enable_working_width_override = tk.BooleanVar(self.root, False)
        self.allow_autosteer = tk.BooleanVar(self.root, True)

        self.get_ip = lambda: None
        self.get_client_port = lambda: None

        self.load_settings(save_data)

        self.construct()

        sv_ttk.set_theme('dark', self.root)
        self.root.mainloop()

    def on_set_log_path(self) -> None:
        path = filedialog.askopenfilename(initialdir=str(Path.home()), defaultextension=".txt", filetypes=[("Text Files", "*.txt")])

        if path is not None:
            self.log_path = path

            save_data = self.get_save_data()
            self.root.destroy()
            self.__init__(save_data)

    def load_defaults(self) -> None:
        print("Loading default settings...")
        self.settings = deepcopy(self.DEFAULTS)
        self.log_path = self.DEFAULTS["log_path"]

    def load_settings(self, save_data: dict = None) -> None:
        try:
            if save_data is None:
                with open("settings.json", "r") as f:
                    self.settings = json.loads(f.read())
            else:
                self.settings = save_data

            self.log_path = self.settings["log_path"]
            self.enable_working_width_override.set(self.settings["enable_working_width_override"])
            self.allow_autosteer.set(self.settings["allow_autosteer"])

        except Exception as e:
            print(f"Error while loading settings: {e}!")
            self.load_defaults()

    def get_save_data(self) -> dict:
        save_data = {
            "log_path": self.log_path,
            "server_port": self.get_server_port(),
            "working_width_override": self.get_working_width_override(),
            "enable_working_width_override": self.enable_working_width_override.get(),
            "allow_autosteer": self.allow_autosteer.get(),
            
            "ip_client": self.get_ip(),
            "port_client": self.get_client_port()
        }

        return save_data

    def save(self) -> None:
        save_data = self.get_save_data()

        with open("settings.json", "w") as f:
            f.write(json.dumps(save_data))

        print("Saved data!")
        messagebox.showinfo("Saved!", "Saved data successfully!")

    def construct(self) -> None:
        self.ui_mgr.Heading("SETTINGS")

        self.ui_mgr.Subheading("\nSERVER")

        self.ui_mgr.Button("Farming simulator log path (log.txt):", "Open", self.on_set_log_path)
        self.ui_mgr.TextInput("   - Log path:", self.log_path, disabled=True)

        self.get_server_port = self.ui_mgr.TextInput("Port:", self.settings["server_port"])

        self.get_working_width_override = self.ui_mgr.TextInput("Working width override (m):", self.settings["working_width_override"])
        self.ui_mgr.Checkbox("Enable working width override:", self.enable_working_width_override)

        self.ui_mgr.Checkbox("Allow autosteer (G29) - Linux only:", self.allow_autosteer)

        self.ui_mgr.Subheading("\nCLIENT")

        self.get_ip = self.ui_mgr.TextInput("Host IP address:", self.settings["ip_client"])
        self.get_client_port = self.ui_mgr.TextInput("Host port:", self.settings["port_client"])

        self.ui_mgr.Heading("")

        ttk.Button(self.root, text="Save settings...", command=self.save).pack()

if __name__ == "__main__":
    Settings()