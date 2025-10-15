from ekfsm.core.components import SysTree
from ekfsm.devices.generic import Device

from .gpio import GPIOExpander


class EKFSurLed(GPIOExpander):
    """
    A class to represent the EKF-SUR-LED devices.
    """

    def __init__(
        self,
        name: str,
        parent: SysTree | None,
        children: list["Device"] | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(name, parent, None, abort, *args, **kwargs)

    def __str__(self) -> str:
        return (
            f"EKFSurLed - GPIO Number: {self.number}; "
            f"sysfs_path: {self.sysfs_device.path if self.sysfs_device else ''}"
        )

    def set(self, led: int, color: str):
        """
        Set the color of a LED.

        Parameters
        ----------
        led : int
            The LED number (0 or 1).
        color : str
            The color of the LED.
            Possible values: "off", "red", "blue", "green", "yellow", "purple", "cyan", "white"
        """
        # 3-color LEDs,
        # 0: Red
        # 1: Blue
        # 2: Green

        if color == "off":
            state = [False, False, False]
        elif color == "red":
            state = [True, False, False]
        elif color == "blue":
            state = [False, True, False]
        elif color == "green":
            state = [False, False, True]
        elif color == "yellow":
            state = [True, True, False]
        elif color == "purple":
            state = [True, False, True]
        elif color == "cyan":
            state = [False, True, True]
        elif color == "white":
            state = [True, True, True]
        else:
            raise ValueError(f"Invalid color: {color}")

        if led < 0 or led > 1:
            raise ValueError(f"Invalid led number: {led}")

        for i in range(3):
            self.set_direction(i + 4 * led, True)
            # Active low
            self.set_pin(i + 4 * led, False if state[i] else True)
