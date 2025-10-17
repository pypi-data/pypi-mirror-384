import contextlib
import inspect
import io
import queue
import re
import socket
import threading
import types
from typing import Any

from universal_mcp.agents.codeact0.utils import derive_context


class Sandbox:
    """
    A class to execute code safely in a sandboxed environment with a timeout.
    """

    def __init__(self, timeout: int = 180):
        """
        Initializes the Sandbox.
        Args:
            timeout: The timeout for code execution in seconds.
        """
        self.timeout = timeout
        self._locals: dict[str, Any] = {}
        self.add_context: dict[str, Any] = {}

    def run(self, code: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """
        Execute code safely with a timeout.
        - Returns (output_str, filtered_locals_dict, new_add_context)
        - Errors or timeout are returned as output_str.
        - Previous variables in _locals persist across calls.
        """

        EXCLUDE_TYPES = (
            types.ModuleType,
            type(re.match("", "")),
            type(threading.Lock()),
            type(threading.RLock()),
            threading.Event,
            threading.Condition,
            threading.Semaphore,
            queue.Queue,
            socket.socket,
            io.IOBase,
        )

        result_container = {"output": "<no output>"}

        def target():
            try:
                with contextlib.redirect_stdout(io.StringIO()) as f:
                    exec(code, self._locals, self._locals)
                result_container["output"] = f.getvalue() or "<code ran, no output printed to stdout>"
            except Exception as e:
                result_container["output"] = "Error during execution: " + str(e)

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(self.timeout)

        if thread.is_alive():
            result_container["output"] = f"Code timeout: code execution exceeded {self.timeout} seconds."

        # Filter locals for picklable/storable variables
        all_vars = {}
        for key, value in self._locals.items():
            if key == "__builtins__":
                continue
            if inspect.iscoroutine(value) or inspect.iscoroutinefunction(value):
                continue
            if inspect.isasyncgen(value) or inspect.isasyncgenfunction(value):
                continue
            if isinstance(value, EXCLUDE_TYPES):
                continue
            if not callable(value) or not hasattr(value, "__name__"):
                all_vars[key] = value

        self._locals = all_vars

        # Safely derive context
        try:
            self.add_context = derive_context(code, self.add_context)
        except Exception:
            # Keep the old context if derivation fails
            pass

        return result_container["output"], self._locals, self.add_context
