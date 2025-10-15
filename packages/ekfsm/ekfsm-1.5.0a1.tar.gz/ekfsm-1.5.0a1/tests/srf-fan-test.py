import pprint
from pathlib import Path

from ekfsm.system import System

config = Path(__file__).parent / "srf-fan-test.yaml"
system = System(config)

pprint.pprint(f"System slots {system.slots}")

system.print()

cpu = system["CPU1"]
cpuB = system.cpu1
cpuC = system[0]

assert cpu == cpuB == cpuC

cpu_slot = system.slots["SYSTEM_SLOT"]
cpu_slotB = system.slots.SYSTEM_SLOT
cpu_slotC = system.slots[0]

assert cpu_slot == cpu_slotB == cpu_slotC

cpu.print()
print(f"probing CPU: {cpu.probe()}")
print(f"inventory: {cpu.inventory.vendor()} {cpu.inventory.model()} {cpu.inventory.serial()}")

srf = system[1]
srf.print()
print(f"probing SRF: {srf.probe()}")
