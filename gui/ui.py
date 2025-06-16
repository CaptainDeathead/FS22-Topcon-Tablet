import tkinter as tk
from tkinter import ttk

class UIManager:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root

    def Heading(self, text: str) -> None:
        heading = ttk.Label(self.root, text=text, font=("Segoe UI", 18, "bold"))
        heading.pack(pady=(10, 5))

    def Subheading(self, text: str) -> None:
        subheading = ttk.Label(self.root, text=text, font=("Segoe UI", 14, "bold"))
        subheading.pack(pady=(0, 15))

    def Checkbox(self, heading: str, variable: tk.BooleanVar) -> None:
        line1 = ttk.Frame(self.root)
        line1.pack(fill='x', pady=5)

        label1 = ttk.Label(line1, text=heading)
        label1.pack(side='left', padx=(10, 0))

        # Add some horizontal padding before checkbox
        checkbox = ttk.Checkbutton(line1, variable=variable)
        checkbox.pack(side='left', padx=(10, 0))

    def TextInput(self, heading: str, initial_value: str, disabled: bool = False) -> object:
        """Returns the function to get the value in the text entry"""

        line2 = ttk.Frame(self.root)
        line2.pack(fill='x', pady=5)

        label2 = ttk.Label(line2, text=heading)
        label2.pack(side='left', padx=(10, 0))

        if disabled:
            state = "readonly"
        else:
            state = "normal"

        entry = ttk.Entry(line2)
        entry.pack(side='left', fill='x', expand=True, padx=(10, 10))

        entry.insert(0, initial_value)
        entry.configure(state=state)

        return entry.get

    def Button(self, heading: str, button_text: str, command: object) -> None:
        line1 = ttk.Frame(self.root)
        line1.pack(fill='x', pady=5)

        label1 = ttk.Label(line1, text=heading)
        label1.pack(side='left', padx=(10, 0))

        # Add some horizontal padding before checkbox
        checkbox = ttk.Button(line1, text=button_text, command=command)
        checkbox.pack(side='left', padx=(10, 0))