# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Module providing dialogs
"""

import customtkinter as ctk

BORDER_WIDTH = 3

# pylint: disable=too-many-ancestors
class ConfimationDialog(ctk.CTkFrame):
    """
    A dialog with a message and Ok / Cancel button
    """
    def __init__(
            self,
            parent,
            message: str,
            show_cancel: bool = True
        ):
        super().__init__(
            parent,
            fg_color=["gray100", "gray20"],
            border_width=BORDER_WIDTH,
            border_color=["gray30", "gray70"]
        )
        self._parent = parent
        self._choice = False

        label = ctk.CTkLabel(self, text=message)
        label.grid(row=0, column=0, sticky="ew", padx=BORDER_WIDTH + 20, pady=BORDER_WIDTH + 10)

        # Buttons
        button_bar = ctk.CTkFrame(self, fg_color="transparent")
        button_bar.grid(row=1, column=0, padx=BORDER_WIDTH, pady=BORDER_WIDTH + 10)

        if show_cancel:
            cancel_btn = ctk.CTkButton(
                button_bar,
                text="Cancel",
                command=lambda: self.close(False)
            )
            cancel_btn.grid(row=0, column=0, sticky='e', padx=20)
            button_bar.columnconfigure(0, weight=1)

        ok_btn = ctk.CTkButton(
            button_bar,
            text="Ok",
            command=lambda: self.close(True)
        )
        ok_btn.grid(row=0, column=1, sticky='e', padx=20)
        button_bar.columnconfigure(1, weight=1)


    def close(self, choice: bool):
        """
        Close this dialog
        """
        self._choice = choice
        self.destroy()


    def wait(self) -> bool:
        """
        Wait for the dialog to be closed and return the result:
        OK = True, Cancel = False
        """
        if self.winfo_exists():
            self.master.wait_window(self)
        return self._choice


class ErrorDialog(ctk.CTkFrame):
    """
    An error dialog with a message and an Ok button
    """
    def __init__(
            self,
            parent,
            message: str
        ):
        super().__init__(
            parent,
            fg_color=["gray100", "gray20"],
            border_width=BORDER_WIDTH,
            border_color=["red3", "red4"]
        )
        self._parent = parent

        label = ctk.CTkLabel(self, text=message)
        label.grid(row=0, column=0, sticky="ew", padx=BORDER_WIDTH + 20, pady=BORDER_WIDTH + 10)

        # Button
        ok_btn = ctk.CTkButton(
            self,
            text="Ok",
            command=self.close
        )
        ok_btn.grid(row=1, column=0, pady=BORDER_WIDTH + 10)


    def close(self):
        """
        Close this dialog
        """
        self.destroy()


    def wait(self):
        """
        Wait for the dialog to be closed .
        """
        if self.winfo_exists():
            self.master.wait_window(self)



# pylint: disable=too-many-ancestors
class MessageDialog(ctk.CTkFrame):
    """
    A dialog with a message without any button
    """
    def __init__(
            self,
            parent,
            message: str
        ):
        super().__init__(
            parent,
            fg_color=["gray100", "gray20"],
            border_width=BORDER_WIDTH,
            border_color=["gray30", "gray70"]
        )
        self._parent = parent

        label = ctk.CTkLabel(self, text=message)
        label.grid(row=0, column=0, sticky="ew", padx=BORDER_WIDTH + 20, pady=BORDER_WIDTH + 10)


    def close(self):
        """
        Close this dialog
        """
        self.destroy()
        if self.winfo_exists():
            self.master.wait_window(self)
