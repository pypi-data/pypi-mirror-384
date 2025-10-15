import os
import re
from abc import ABC, abstractmethod
from pathlib import Path

import gpiod
from gpiod.line import Direction, Value
from gpiod.line_settings import LineSettings
from more_itertools import first_true

from ekfsm.core.components import SysTree
from ekfsm.exceptions import GPIOError
from ekfsm.log import ekfsm_logger

from ..core.probe import ProbeableDevice
from .generic import Device

gpio_pat = re.compile(r"gpiochip\d+")


def get_gpio_major_minor(path: Path) -> tuple[int, int]:
    for d in path.iterdir():
        if gpio_pat.match(d.name):
            dev = d / "dev"
            if dev.exists():
                content = dev.read_text().strip()
                try:
                    major, minor = map(int, content.split(":"))
                except Exception as e:
                    raise GPIOError(
                        GPIOError.ErrorType.NO_MAJOR_MINOR,
                        f"No minor/major number found for GPIO device at {path}",
                    ) from e
                return major, minor

    raise GPIOError(
        GPIOError.ErrorType.NO_MAJOR_MINOR,
        f"No minor/major number found for GPIO device at {path}",
    )


def find_gpio_dev_with_major_minor(major: int, minor: int) -> Path | None:
    for dev in Path("/dev").iterdir():
        if gpio_pat.match(dev.name):
            stat_info = dev.stat()

            cmaj = os.major(stat_info.st_rdev)
            cmin = os.minor(stat_info.st_rdev)

            if cmaj == major and cmin == minor:
                return dev

    raise GPIOError(
        GPIOError.ErrorType.NO_MATCHING_DEVICE,
        f"Failed to find GPIO device with major {major} and minor {minor}",
    )


class GPIO(Device):
    def __init__(
        self,
        name: str,
        parent: SysTree | None = None,
        children: Device | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(
            name,
            parent,
            None,
            abort,
            *args,
            **kwargs,
        )
        self.logger = ekfsm_logger("GPIODevice" + name)
        major, minor = self._find_gpio_dev(parent, *args, **kwargs)
        self.gpio = find_gpio_dev_with_major_minor(major, minor)

        assert self.gpio is not None
        match = re.search(r"\d+", self.gpio.name)

        if not match:
            raise GPIOError(GPIOError.ErrorType.NO_MATCHING_DEVICE, "Failed to find matching device")

        self.number: int = int(match.group().strip())

        self.init_dev()

    def _find_gpio_dev(self, parent: SysTree | None = None, *args, **kwargs) -> tuple[int, int]:
        self.addr = self.get_i2c_chip_addr()
        self.logger.debug(f"GPIO: {self.addr}")
        self.sysfs_device = self.get_i2c_sysfs_device(self.addr)
        return get_gpio_major_minor(self.sysfs_device.path)

    def init_dev(self):
        if self.gpio:
            try:
                self.dev = gpiod.Chip(str(self.gpio))
                self.initialized = True
                return
            except FileNotFoundError:
                self.initialized = False
                raise FileNotFoundError(f"{self.gpio} does not exist")

        self.initialized = False

    def num_lines(self) -> int:
        """
        Get number of GPIO lines available on the device.
        """
        return self.dev.get_info().num_lines

    def set_pin(self, pin: int, value: bool) -> None:
        """
        Set the value of a GPIO pin.

        Parameters
        ----------
        pin : int
            The pin number.
        value : bool
            The value to set.
        """
        v = Value.ACTIVE if value else Value.INACTIVE
        with self.dev.request_lines(
            consumer="set-pin",
            config={pin: gpiod.LineSettings()},
        ) as request:
            request.set_value(pin, v)

    def get_pin(self, pin: int) -> bool:
        """
        Get the value of a GPIO pin.

        Parameters
        ----------
        pin : int
            The pin number.

        Returns
        -------
        bool
            The value of the pin.
        """
        with self.dev.request_lines(
            consumer="get-pin",
            config={pin: gpiod.LineSettings()},
        ) as req:
            value = req.get_value(pin)
            return value == Value.ACTIVE

    def get_lines(self, lines: list[int]):
        if (
            invalid_pin := first_true(
                lines,
                pred=lambda line: line < 0 or line >= self.num_lines(),
                default=None,
            )
        ) is not None:
            raise GPIOError(GPIOError.ErrorType.INVALID_PIN, f"GPIO {invalid_pin} is invalid.")

    def set_direction(self, pin: int, direction: bool) -> None:
        """
        Set the direction of a GPIO pin.

        Parameters
        ----------
        pin : int
            The pin number.
        direction : bool
            The direction to set. True for output, False for input.
        """
        dir = Direction.OUTPUT if direction else Direction.INPUT
        self.dev.request_lines(
            consumer="set-direction",
            config={pin: LineSettings(direction=dir)},
        )

    def __str__(self) -> str:
        return (
            f"GPIO - Number: {self.number}; "
            f"sysfs_path: {self.sysfs_device.path if self.sysfs_device else ''} "
            f"(dev: {self.gpio if self.gpio else 'No matching device found'})"
        )


class GPIOExpander(GPIO):
    def __init__(
        self,
        name: str,
        parent: SysTree | None,
        children: Device | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(name, parent, None, abort, *args, **kwargs)

    def __str__(self) -> str:
        return (
            f"GPIOExpander - Number: {self.number}; "
            f"sysfs_path: {self.sysfs_device.path if self.sysfs_device else ''}"
        )


class EKFIdentificationIOExpander(GPIOExpander, ProbeableDevice):
    def __init__(
        self,
        name: str,
        parent: SysTree | None,
        children: Device | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(name, parent, None, abort, *args, **kwargs)

    def probe(self, *args, **kwargs) -> bool:
        from ekfsm.core import HWModule

        assert isinstance(self.hw_module, HWModule)
        id, _ = self.read_board_id_rev()
        self.logger.debug(f"Probing EKFIdentificationIOExpander: {id}")

        return self.hw_module.id == id

    def read_board_id_rev(self) -> tuple[int, int]:
        for pin in range(6, 8):
            self.set_direction(pin, True)
            self.set_pin(pin, False)
        for pin in range(0, 6):
            self.set_direction(pin, False)

        v_gnd = self.read_id_gpio_inputs()
        self.set_pin(7, True)
        v_7h = self.read_id_gpio_inputs()
        self.set_pin(6, True)
        v_6h = self.read_id_gpio_inputs()

        readings = [v_gnd, v_7h, v_6h]
        bit_sums = []
        for bit in range(5, -1, -1):
            s = 0
            for reading in readings:
                s += (reading >> bit) & 1
            bit_sums.append(s)

        return (
            sum(val * (4**i) for i, val in enumerate(reversed(bit_sums[2:]))),
            self._get_board_rev(bit_sums[:2]),  # board_rev
        )

    def revision(self) -> str:
        _, rev = self.read_board_id_rev()
        return str(rev)

    def read_id_gpio_inputs(self) -> int:
        value = 0
        for pin in range(6):
            if self.get_pin(pin):
                value |= 1 << pin

        return value

    @staticmethod
    def _get_board_rev(bits: list[int]) -> int:
        """Convert 2-bit sum values to board revision number."""
        rev_map = {
            (0, 0): 0,
            (0, 1): 1,
            (0, 2): 2,
            (1, 0): 3,
            (1, 1): 4,
            (1, 2): 5,
            (2, 0): 6,
            (2, 1): 7,
            (2, 2): 8,
        }
        return rev_map.get((bits[0], bits[1]), -1)

    def __str__(self) -> str:
        return (
            f"EKFIdentificationIOExpander - Number: {self.number}; "
            f'sysfs_path: {self.sysfs_device.path if self.sysfs_device else ""}'
        )


class SimGpio(ABC):
    @abstractmethod
    def num_lines(self) -> int:
        pass

    @abstractmethod
    def set_pin(self, pin: int, value: bool) -> None:
        pass

    @abstractmethod
    def get_pin(self, pin: int) -> bool:
        pass

    @abstractmethod
    def set_direction(self, pin: int, direction: bool) -> None:
        pass


class EKFIdSimGpio(SimGpio):
    def __init__(self, coding_gnd, coding_vcc, coding_6, coding_7) -> None:
        self._coding_gnd = coding_gnd
        self._coding_vcc = coding_vcc
        self._coding_6 = coding_6
        self._coding_7 = coding_7
        self._dir = 0
        self._out = 0
        self._in = 0

    def num_lines(self) -> int:
        return 8

    def set_pin(self, pin: int, value: bool) -> None:
        mask = 1 << pin
        if value not in [0, 1]:
            raise RuntimeError("value must be 0 or 1")
        if self._dir & mask:
            self._out = (self._out & ~mask) | (value << pin)
        else:
            raise RuntimeError("pin not set as output")

    def get_pin(self, pin: int) -> bool:
        mask = 1 << pin
        if self._coding_gnd & mask:
            return False
        if self._coding_vcc & mask:
            return True
        if self._coding_6 & mask:
            return True if self._out & (1 << 6) else False
        if self._coding_7 & mask:
            return True if self._out & (1 << 7) else False
        return False

    def set_direction(self, pin: int, direction: bool) -> None:
        if direction == 1 and (pin != 6 and pin != 7):
            raise RuntimeError("only pins 6 and 7 supported as output")
        mask = 1 << pin
        if direction:
            self._dir |= mask
        else:
            self._dir &= ~mask
