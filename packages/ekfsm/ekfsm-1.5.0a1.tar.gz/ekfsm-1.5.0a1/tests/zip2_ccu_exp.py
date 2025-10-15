import logging

# import time
from pathlib import Path

from ekfsm.system import System

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

config = Path(__file__).parent / "zip2-ccu-only.yaml"
system = System(config)

cpu = system[0]

ccu = system.ccu

# get parameterset
params = ccu.management.get_parameterset()
print(f"Parameterset: {params}")

# Firmware download
# def progress_callback(offset):
#     print(f"Loading firmware: {offset}")

# with open("/home/klaus/fw-ccu-00-default.bin", "rb") as f:
#     firmware = f.read()
#     ccu.management.load_firmware(firmware, progress_callback)
# time.sleep(5)

# Identify firmware
# print(f"CCU firmware: {ccu.management.identify_firmware()}")

# Fan control
# while True:
#     cputemp = cpu.th.cputemp()
#     print(f"CPU temperature: {cputemp}")
#     ccu.fan.push_temperature(-1, cputemp)
#     time.sleep(1)
#     fan_status = ccu.fan.fan_status(0)
#     print(f"Fan status0: {fan_status}")
#     fan_status = ccu.fan.fan_status(1)
#     print(f"Fan status1: {fan_status}")

# CCU Restart
# ccu.management.restart()

# # WD Trigger
# while True:
#     ccu.sysstate.wd_trigger()
#     time.sleep(5)
