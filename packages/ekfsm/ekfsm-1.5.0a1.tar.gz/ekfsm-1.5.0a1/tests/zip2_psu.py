import logging
import time
from pathlib import Path

from ekfsm.system import System

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

config = Path(__file__).parent / "zip2-comp1.yaml"
system = System(config)

psu = system.psu

print(f"vendor: {psu.inventory.vendor()}")
print(f"model: {psu.inventory.model()}")
print(f"serial: {psu.inventory.serial()}")
print(f"revision: {psu.inventory.revision()}")


def print_psu_block(block_name, block):
    print(f"block: {block_name}")
    print(f"voltage: {block.voltage()}")
    print(f"current: {block.current()}")
    print(f"status: {block.status()}")


while True:
    print(f"temperature: {psu.th.temperature()}")
    print_psu_block("main (+12V)", psu.main)
    print_psu_block("sby (+5V)", psu.sby)
    time.sleep(0.5)
