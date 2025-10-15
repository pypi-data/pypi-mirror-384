import socket
import struct
from pathlib import Path
from typing import List
from unittest.mock import patch

from smbus2 import SMBus

from ekfsm.devices.gpio import EKFIdSimGpio, SimGpio
from ekfsm.devices.smbus import SimSMBus

from .core.components import SysTree
from .core.sysfs import set_sysfs_root
from .devices import GPIO

GPIO_SIM_MAPPING: dict[str, SimGpio] = {}
SMBUS_SIM_MAPPING: dict[str, SimSMBus] = {}


def register_gpio_sim(major: int, minor: int, sim_gpio: SimGpio) -> None:
    name = f"{major}:{minor}"
    if name in GPIO_SIM_MAPPING:
        raise ValueError(f"GPIO_SIM_MAPPING already contains {name}")
    GPIO_SIM_MAPPING[name] = sim_gpio


def find_gpio_dev_with_major_minor(major: int, minor: int) -> SimGpio:
    name = f"{major}:{minor}"
    if name not in GPIO_SIM_MAPPING:
        raise ValueError(f"GPIO_SIM_MAPPING does not contain {name}")
    return GPIO_SIM_MAPPING[name]


def register_smbus_sim(bus_num: int, i2c_addr: int, sim_smbus: SimSMBus) -> None:
    name = f"{bus_num}:{i2c_addr}"
    if name in SMBUS_SIM_MAPPING:
        raise ValueError(f"SMBUS_SIM_MAPPING already contains {name}")
    SMBUS_SIM_MAPPING[name] = sim_smbus


def find_smbus_dev(bus_num: int, i2c_addr: int) -> SimSMBus:
    name = f"{bus_num}:{i2c_addr}"

    if name not in SMBUS_SIM_MAPPING:
        raise ValueError(f"SMBUS_SIM_MAPPING does not contain {name}")
    return SMBUS_SIM_MAPPING[name]


class GPIOSimulator(GPIO):
    def __init__(
        self,
        name: str,
        parent: SysTree | None = None,
        *args,
        **kwargs,
    ):
        super(GPIO, self).__init__(
            name,
            parent,
            *args,
            **kwargs,
        )
        major, minor = self._find_gpio_dev(parent, *args, **kwargs)
        self._sim_gpio = find_gpio_dev_with_major_minor(major, minor)
        self.number = minor

    def num_lines(self) -> int:
        return self._sim_gpio.num_lines()

    def set_pin(self, pin: int, value: bool) -> None:
        self._sim_gpio.set_pin(pin, value)

    def get_pin(self, pin: int) -> bool:
        return self._sim_gpio.get_pin(pin)

    def set_direction(self, pin: int, direction: bool) -> None:
        self._sim_gpio.set_direction(pin, direction)

    def __str__(self) -> str:
        return f"GPIO_SIM({self.name})"


class SMBusSimulator:
    def __init__(self, bus_num: int):
        self.bus_num = bus_num

    def read_word_data(self, i2c_addr: int, cmd: int) -> int:
        return find_smbus_dev(self.bus_num, i2c_addr).read_word_data(cmd)

    def read_block_data(self, i2c_addr: int, cmd: int) -> List[int]:
        return find_smbus_dev(self.bus_num, i2c_addr).read_block_data(cmd)

    def write_block_data(self, i2c_addr: int, cmd: int, data: List[int]):
        find_smbus_dev(self.bus_num, i2c_addr).write_block_data(cmd, data)

    def write_byte(self, i2c_addr: int, cmd: int):
        find_smbus_dev(self.bus_num, i2c_addr).write_byte(cmd)

    def write_word_data(self, i2c_addr: int, cmd: int, data: int):
        find_smbus_dev(self.bus_num, i2c_addr).write_word_data(cmd, data)


def patch_methods(cls, simulator, methods):
    patched = []
    for i, method in enumerate(methods):
        if hasattr(cls, method) and hasattr(simulator, method):
            patched.append(patch.object(cls, method, new_callable=lambda: getattr(simulator, method)))
            patched[i].start()


def enable_simulation(sysfs_path: Path | str) -> None:
    global GPIO_SIM_MAPPING
    GPIO_SIM_MAPPING = {}

    global SMBUS_SIM_MAPPING
    SMBUS_SIM_MAPPING = {}

    if isinstance(sysfs_path, str):
        sysfs_path = Path(sysfs_path)

    set_sysfs_root(sysfs_path)
    patch_methods(
        GPIO,
        GPIOSimulator,
        ["__init__", "num_lines", "set_pin", "get_pin", "set_direction", "__str__"],
    )
    patch_methods(
        SMBus,
        SMBusSimulator,
        [
            "__init__",
            "read_word_data",
            "read_block_data",
            "write_block_data",
            "write_byte",
            "write_word_data",
        ],
    )


def register_gpio_simulations():
    register_gpio_sim(233, 1, EKFIdSimGpio(0x38, 0x1, 0x0, 0x6))  # SRF Rev 0
    register_gpio_sim(233, 2, EKFIdSimGpio(0x34, 0xA, 0x0, 0x1))  # CCU Rev 0


class SocketSmbus(SimSMBus):
    def __init__(self, host: str, port: int) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def read_word_data(self, cmd: int) -> int:
        req = struct.pack("BB", 0x4, cmd)
        self.sock.send(req)
        data = self.sock.recv(2)
        return struct.unpack("<H", data)[0]

    def read_block_data(self, cmd: int) -> List[int]:
        req = struct.pack("BB", 0x1, cmd)
        self.sock.send(req)
        _count = self.sock.recv(1)
        count = struct.unpack("B", _count)[0]
        data = self.sock.recv(count)
        return [int(data[i]) for i in range(0, len(data), 1)]

    def write_block_data(self, cmd: int, data: List[int]):
        _data = bytes(data)
        hdr = struct.pack("BBB", 0x2, cmd, len(_data))
        self.sock.send(hdr + _data)

    def write_byte(self, cmd: int):
        hdr = struct.pack("BB", 0x3, cmd)
        self.sock.send(hdr)

    def write_word_data(self, cmd: int, data: int):
        hdr = struct.pack("BBH", 0x5, cmd, data)
        self.sock.send(hdr)
