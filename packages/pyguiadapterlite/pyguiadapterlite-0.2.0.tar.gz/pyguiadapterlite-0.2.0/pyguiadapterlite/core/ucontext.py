import threading
from tkinter import Tk, TclError
from typing import Optional

from pyguiadapterlite.utils import _exception


class UContext(object):
    _tk_instance: Optional[Tk] = None
    _fn_execute_window = None
    _current_cancel_event: Optional[threading.Event] = None

    @classmethod
    def app_started(cls, tk_instance: Tk):
        cls._tk_instance = tk_instance

    @classmethod
    def app_quit(cls):
        cls._tk_instance = None

    @classmethod
    def app_instance(cls) -> Optional[Tk]:
        return cls._tk_instance

    @classmethod
    def reset(cls):
        if cls._tk_instance:
            try:
                cls._tk_instance.destroy()
            except TclError as e:
                _exception(e, "failed to destroy tk instance")
        cls._tk_instance = None
        cls._fn_execute_window = None
        cls._current_cancel_event = None

    @classmethod
    def execute_window_created(cls, window):
        cls._fn_execute_window = window

    @classmethod
    def execute_window_closed(cls):
        cls._fn_execute_window = None

    @classmethod
    def current_execute_window(cls):
        return cls._fn_execute_window

    @classmethod
    def current_cancel_event(cls) -> Optional[threading.Event]:
        return cls._current_cancel_event

    @classmethod
    def current_thread_created(cls, cancel_event: threading.Event):
        cls._current_cancel_event = cancel_event

    @classmethod
    def current_thread_finished(cls):
        cls._current_cancel_event = None
