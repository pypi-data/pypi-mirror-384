import logging
from pathlib import Path

from ekfsm.system import HWModule, System

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def print_inventory(name, inventory):
    print(f"{name}: {inventory.vendor()} {inventory.model()} {inventory.serial()}")


def probe_and_print_inventory(board: HWModule):
    board.probe()
    print_inventory(board.name, board.inventory)


config = Path(__file__).parent / "zip2-comp2.yaml"
system = System(config, abort=False)
print(system)

_psu = system.psu
probe_and_print_inventory(_psu)

_cpu = system.cpu
probe_and_print_inventory(_cpu)

_lan = system.lan
probe_and_print_inventory(_lan)

_ssd1 = system.ssd1
probe_and_print_inventory(_ssd1)

_ser = system.ser
probe_and_print_inventory(_ser)

_ssd2 = system.ssd2
probe_and_print_inventory(_ssd2)

_ssd3 = system.ssd3
probe_and_print_inventory(_ssd3)

_info = system.info
probe_and_print_inventory(_info)

# _ccu = system.ccu
# probe_and_print_inventory(_ccu)


# SUR LED Test
_ser.led_a.set(0, "red")
_ser.led_a.set(1, "yellow")
_ser.led_c.set(0, "white")
_ser.led_d.set(1, "blue")

print(f"SUR TEMP: {_ser.th.temperature()}")
print(f"SUR HUMIDITY: {_ser.th.humidity()}")


# # CCU Test
# # chassis inventory via ccu object
# print_inventory("chassis", _ccu.chassis_inventory)
# # alternative way to get chassis inventory
# print_inventory("chassis", system.inventory)

# print(f"CCU firmware: {_ccu.management.identify_firmware()}")
