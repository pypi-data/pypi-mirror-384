# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Provides the ApplicationManager class as the root window
"""

from pathlib import Path
import os

import tkinter
import customtkinter as ctk
from PIL import ImageTk

import qat
from qat.gui.application_manager.toolbar import ToolBar
from qat.gui.application_manager.editor import EditorArea
from qat.gui.stack_layout import StackLayout
from qat.gui.dialogs import ConfimationDialog, ErrorDialog, MessageDialog
from qat.gui.spy.window import SpyWindow


class ApplicationManager(ctk.CTk):
    """
    Show a GUI to manage applications
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure root window
        current_path = Path(os.path.dirname(__file__)).resolve().absolute()
        try:
            image_dir = current_path.parent / 'images'
            if qat.app_launcher.is_windows():
                self.iconbitmap(image_dir / "qat_icon.ico")
            self.iconphoto(True, ImageTk.PhotoImage(file=image_dir / "icon.png"))
        except tkinter.TclError:
            # Icons may not be supported on some platforms
            pass
        self.title('Qat Application Manager')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.geometry("1000x270")

        # Select custom theme
        theme_file = Path(os.path.dirname(
            __file__)).resolve().absolute().parent / 'theme.json'
        ctk.set_default_color_theme(str(theme_file))

        # Initialize GUI
        self._main_stack = StackLayout(self)
        self._main_stack.grid(row=0, column=0, sticky='nsew')
        self._main_stack.grid_rowconfigure(0, weight=1)
        self._main_stack.grid_columnconfigure(0, weight=1)

        # Main frame with normal content
        main_frame = ctk.CTkFrame(self._main_stack)
        main_frame.grid(row=0, column=0, sticky='nsew')
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self._toolbar = ToolBar(main_frame, self.open_spy, self.show_ok_cancel_dlg)
        self._toolbar.grid(row=0, column=0, sticky='new', padx=5, pady=5)
        self._editor_area = EditorArea(main_frame, self.show_ok_cancel_dlg)
        self._editor_area.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

        # "overlay" frame to display "dialogs"
        self._overlay = ctk.CTkFrame(self._main_stack, fg_color="transparent")
        self._overlay.grid(row=0, column=0, sticky='nsew')
        self._overlay.grid_rowconfigure(0, weight=1)
        self._overlay.grid_columnconfigure(0, weight=1)

        self._main_stack.add('overlay', self._overlay)
        self._main_stack.add('main', main_frame)

        # Register callbacks
        self._toolbar.register_app_changed(self._editor_area.set_app)
        self._toolbar.register_new_app(lambda: self._editor_area.set_app(''))
        self._editor_area.register_app_modified(self._toolbar.select_app)


    def show_ok_cancel_dlg(self, message: str, show_cancel: bool = True) -> bool:
        """
        Display an ok/cancel dialog and return the result.
        """
        dlg = ConfimationDialog(self._overlay, message, show_cancel)
        dlg.grid(row=0, column=0)
        self._main_stack.show('overlay')
        result = dlg.wait()
        self._main_stack.show('main')
        return result


    def show_error(self, message: str) -> bool:
        """
        Display an error dialog and wait for it to be closed.
        """
        dlg = ErrorDialog(self._overlay, message)
        dlg.grid(row=0, column=0)
        self._main_stack.show('overlay')
        dlg.wait()
        self._main_stack.show('main')
        return False


    def show_message(self, message: str) -> MessageDialog:
        """
        Display an error dialog and return it.
        """
        dlg = MessageDialog(self._overlay, message)
        dlg.grid(row=0, column=0)
        self._main_stack.show('overlay')
        return dlg


    def open_spy(self, app_name: str, attach: bool = False):
        """
        Open the Spy window
        """
        dialog = self.show_message(f'Loading application "{app_name}" ...')
        self.update()
        try:
            if attach:
                qat.attach_to_application(app_name)
            else:
                qat.start_application(app_name)
            qat.unlock_application()
        except Exception as error: # pylint: disable=broad-exception-caught
            dialog.close()
            self.show_error(str(error))
            return

        self.withdraw()
        dialog.close()
        self._main_stack.show('main')
        spy_window = SpyWindow()
        self.wait_window(spy_window)
        try:
            if attach:
                qat.deactivate_picker()
                qat.detach()
            elif qat.current_application_context().is_running():
                qat.close_application()
        except Exception as error: # pylint: disable=broad-exception-caught
            print(f'Unable to close application: {error}')
        self.deiconify()


if __name__ == "__main__":
    app = ApplicationManager()
    app.mainloop()
