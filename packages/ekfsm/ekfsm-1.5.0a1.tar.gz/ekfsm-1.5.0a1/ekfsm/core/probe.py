from abc import ABC, abstractmethod


class ProbeableDevice(ABC):
    @abstractmethod
    def probe(self, *args, **kwargs) -> bool:
        """
        Probe the hardware device to check if it is present and if it is the correct device.
        """
        pass
