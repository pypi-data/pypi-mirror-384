"""
Some devices or device functions don't allow concurrent access.
The locking mechanism is used to ensure that only one process/thread can
access the device (function) at a time.

Locking granularity is defined by the device.
It may be at the device level or function level.

Application can choose to use the locking mechanism or not.
By default, the locking mechanism is enabled and uses the default
lockfile root directory ``/var/lock/ekfsm``.

Use :func:`locking_configure` to enable or disable the locking mechanism or to change
the lockfile root directory.
"""

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path

USE_LOCK = True
LOCKFILE_ROOT = "/var/lock/ekfsm"
ALL_LOCKERS: list["Locker"] = []  # List of all locker instances


def locking_configure(enable: bool, lockfile_root: str = LOCKFILE_ROOT):
    """
    Configures the locking mechanism.

    Parameters
    ----------
    enable
        Whether to enable or disable locking.
    lockfile_root
        The root directory for lockfiles.
    """
    global USE_LOCK, LOCKFILE_ROOT
    USE_LOCK = enable
    LOCKFILE_ROOT = lockfile_root


def locking_cleanup():
    """
    Cleans up all lockfiles and closes all lock file descriptors.
    Should be called at the end of the program to ensure all locks are released.
    """
    for locker in ALL_LOCKERS:
        locker.cleanup()


class Locker:
    """
    A class that implements a locking mechanism using file locks.

    Parameters
    ----------
    module
        The name of the module or resource to lock. This will be used to create a unique lock file.

    Example
    -------
    .. code-block:: python

        with Locker("mysharedresourcename").lock():
            # Access the shared resource here
            pass

    """

    def __init__(self, module: str):
        if not USE_LOCK:
            return

        self.lockfile_path = Path(LOCKFILE_ROOT) / module
        self.lock_fd = None
        # Ensure lockfile exists
        os.makedirs(LOCKFILE_ROOT, exist_ok=True)
        open(self.lockfile_path, "a").close()
        ALL_LOCKERS.append(self)

    def cleanup(self):
        """
        Cleans up the lock file and closes the lock file descriptor.

        Important
        ---------
        This method should be called when the lock is no longer needed.

        Note
        ----
        It is automatically called when the context manager exits.
        """
        if not USE_LOCK:
            return
        if self.lock_fd is not None:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                os.close(self.lock_fd)
                self.lock_fd = None
            except (OSError, AttributeError):
                pass

    @contextmanager
    def lock(self):
        """
        Locks the resource for exclusive access.

        Note
        ----
        This method is a context manager that locks the resource when entered
        and releases the lock when exited.
        """
        if not USE_LOCK:
            yield
        self.lock_fd = os.open(self.lockfile_path, os.O_RDWR)
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX)
            yield
        finally:
            self.cleanup()
