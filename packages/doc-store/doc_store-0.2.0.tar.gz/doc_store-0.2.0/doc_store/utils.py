import getpass
import os
import threading
from concurrent.futures import ThreadPoolExecutor


class BlockingThreadPool(ThreadPoolExecutor):
    """A thread pool that blocks submission
    if the maximum number of workers is reached."""

    def __init__(
        self,
        max_workers=None,
        thread_name_prefix="",
        initializer=None,
        initargs=(),
    ):
        super().__init__(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
            initializer=initializer,
            initargs=initargs,
        )
        print(f"max_workers={self._max_workers}")
        self._semaphore = threading.Semaphore(self._max_workers)

    def submit(self, fn, /, *args, **kwargs):
        self._semaphore.acquire()
        future = super().submit(fn, *args, **kwargs)
        future.add_done_callback(lambda _: self._semaphore.release())
        return future


def get_username() -> str:
    """Get the current user name."""
    username = getpass.getuser()
    if not username:
        username = os.getlogin()
    if not username:
        username = "unknown"
    return username


def secs_to_readable(secs: int) -> str:
    """Convert seconds to a human-readable format."""
    hours, secs = secs // 3600, secs % 3600
    minutes, secs = secs // 60, secs % 60
    # return in 01:11:30 format
    return f"{hours:02}:{minutes:02}:{secs:02}"
