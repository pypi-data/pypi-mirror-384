from contextlib import redirect_stdout
import io


class BufferPrint:
    """
    print but buffer the output
    useful to replace the module's print method.
    """

    def __init__(self):
        self._buffer = io.StringIO()

    def print(self, *args, **kwargs):
        with self._buffer as buffer, redirect_stdout(buffer):
            print(*args, **kwargs)

    def buffer(self) -> str:
        return self._buffer.getvalue()
