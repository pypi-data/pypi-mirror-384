import logging
import time
from pathlib import Path

from ekfsm.system import System

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

config = Path(__file__).parent / "zip2-ccu-only.yaml"
system = System(config)

cpu = system[0]
print(f"probing CPU: {cpu.probe()}")
print(f"inventory: {cpu.inventory.vendor()} {cpu.inventory.model()} {cpu.inventory.serial()}")

ccu = system.ccu


while True:
    sample, more_samples = ccu.imu.sample()
    if sample is not None:
        print(f"accel: {sample.accel}, gyro: {sample.gyro}, lost: {sample.lost} more: {more_samples}")
        time.sleep(0.01)
