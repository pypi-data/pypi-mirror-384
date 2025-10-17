# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Qat Spy application
"""


from qat.gui.application_manager.window import ApplicationManager


def open_gui():
    """
    Open the main window
    """
    app = ApplicationManager()
    app.mainloop()


if __name__ == "__main__":
    open_gui()
