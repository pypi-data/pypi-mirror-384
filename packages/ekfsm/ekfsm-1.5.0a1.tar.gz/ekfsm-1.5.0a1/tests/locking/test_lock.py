import subprocess
import sys
import time

import pytest

# start 2 times test_lock.py and wait for them to finish


def test_locking():
    """
    Test the locking mechanism by running two instances of the same script in parallel.
    """

    # Start the first instance
    proc1 = subprocess.Popen([sys.executable, "tests/locking/lock_tester.py", "1"])
    time.sleep(1)  # Give it some time to start

    # Start the second instance
    proc2 = subprocess.Popen([sys.executable, "tests/locking/lock_tester.py", "2"])

    # Wait for both processes to finish
    proc1.wait()
    proc2.wait()

    assert proc1.returncode == 0
    assert proc2.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__])
