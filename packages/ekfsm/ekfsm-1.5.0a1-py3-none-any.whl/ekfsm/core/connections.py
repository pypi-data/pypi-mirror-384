from contextlib import contextmanager


class Connectable:

    def __init__(self, client=None):
        self._client = client
        self._connected = False

    @contextmanager
    def connect(self):
        if not self._connected:
            client = self._client(self.service_addr, command_timeout=self.timeout)
            self._connected = True
        try:
            yield client
        finally:
            client.close()
            del client
