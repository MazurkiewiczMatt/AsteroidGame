import tkinter as tk

from constants import *

# ----------------------------------------------------------------------
# Reusable Action Button class (unchanged)
# ----------------------------------------------------------------------
class GameActionButton(tk.Button):
    """
    A button that automatically shows or hides itself based on a condition.
    """
    def __init__(self, parent, label, command, condition, pack_opts=None, **kwargs):
        super().__init__(parent, text=label, command=command, **kwargs)
        self.condition = condition
        self.pack_opts = pack_opts if pack_opts is not None else {}

    def update_visibility(self):
        if self.condition():
            if not self.winfo_ismapped():
                self.pack(**self.pack_opts)
        else:
            if self.winfo_ismapped():
                self.pack_forget()


# ----------------------------------------------------------------------
# Action Panel class (unchanged)
# ----------------------------------------------------------------------
class ActionPanel(tk.LabelFrame):
    """
    A panel that contains a collection of GameActionButtons.
    """
    def __init__(self, parent, title, actions, **kwargs):
        super().__init__(parent, text=title, **kwargs)
        self.action_buttons = []
        for (label, callback, condition) in actions:
            btn = GameActionButton(
                self, label, callback, condition,
                pack_opts={"side": "left", "padx": UI_PADDING_SMALL},
                bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL
            )
            self.action_buttons.append(btn)
            btn.pack(**btn.pack_opts)

    def update_buttons(self):
        for btn in self.action_buttons:
            btn.update_visibility()