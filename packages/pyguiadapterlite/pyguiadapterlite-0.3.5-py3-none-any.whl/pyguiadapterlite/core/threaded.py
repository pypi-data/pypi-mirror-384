import threading
from typing import Dict, Any, Optional

from pyguiadapterlite.core.fn import BaseFunctionExecutor, FnInfo, ExecuteStateListener
from pyguiadapterlite.core.ucontext import UContext
from pyguiadapterlite.utils import _exception


class ThreadRunningException(RuntimeError):
    pass


class ThreadedExecutor(BaseFunctionExecutor):

    def __init__(self, listener: Optional[ExecuteStateListener] = None):
        super().__init__(listener)
        self._is_executing = False
        self._current_thread = None
        self._cancel_event = threading.Event()
        self._state_lock = threading.Lock()

    def execute(self, fn_info: FnInfo, arguments: Optional[Dict[str, Any]] = None):
        with self._state_lock:
            if self._is_executing:
                raise ThreadRunningException("a function is already executing")
            # 重置状态
            self._is_executing = True
            self._cancel_event.clear()
            UContext.current_thread_created(self._cancel_event)

        # 必要的检查
        if not UContext.app_instance():
            raise RuntimeError("tkinter is not initialized yet")

        if self._listener:
            # 回调before_execute()，该方法在主线程中执行
            self._listener.before_execute(fn_info, arguments)
        # 启动线程执行目标函数
        self._current_thread = threading.Thread(
            target=self._execute_in_thread, args=(fn_info, arguments), daemon=True
        )
        self._current_thread.start()

    @property
    def is_cancelled(self) -> bool:
        with self._state_lock:
            if not self._is_executing:
                return False
            return self._cancel_event.is_set()

    @property
    def is_executing(self) -> bool:
        with self._state_lock:
            return self._is_executing

    def try_cancel(self):
        if not self.is_executing or self.is_cancelled:
            return
        with self._state_lock:
            self._cancel_event.set()

    def _on_finish(
        self,
        fn_info: FnInfo,
        arguments: Dict[str, Any],
        return_value: Any,
        exception: Optional[BaseException],
    ):
        def _callback():
            self._is_executing = False
            self._cancel_event.clear()
            self._current_thread = None
            if self._listener:
                self._listener.on_execute_finish(
                    fn_info, arguments, return_value, exception
                )

        tk_instance = UContext.app_instance()
        assert tk_instance is not None
        tk_instance.after(0, _callback)

    def _on_start(self, fn_info: FnInfo, arguments: Dict[str, Any]):
        tk_instance = UContext.app_instance()
        assert tk_instance is not None
        if self._listener:
            tk_instance.after(0, self._listener.on_execute_start, fn_info, arguments)

    def _execute_in_thread(self, fn_info: FnInfo, arguments: Dict[str, Any]):
        # 注意该方法会在子线程中被调用
        try:
            arguments = arguments or {}
            self._on_start(fn_info, arguments)
            fn = fn_info.fn
            arguments = arguments.copy()
            result = fn(**arguments)
            self._on_finish(fn_info, arguments, result, None)
        except SystemExit as e:
            _exception(e, "SystemExit caught in function execution thread")
            if fn_info.capture_system_exit_exception:
                self._on_finish(fn_info, arguments, None, e)
            else:
                tk_instance = UContext.app_instance()
                if not tk_instance:
                    exit(e.code)
                else:
                    tk_instance.after(0, tk_instance.quit)
        except BaseException as e:
            self._on_finish(fn_info, arguments, None, e)
