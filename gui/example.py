import tkinter as tk
import sv_ttk
from tkinter import ttk

from ui import UIManager

root = tk.Tk()
root.title("Example")
root.geometry("400x300")

ui_mgr = UIManager(root)

ui_mgr.Heading("HEADING")
ui_mgr.Subheading("SUBHEADING")

checkbox_var = tk.BooleanVar(value=True)
ui_mgr.Checkbox("Checkbox test:", checkbox_var)

get_val = ui_mgr.TextInput("Textinput test:")

sv_ttk.set_theme('dark', root)
tk.mainloop()
