import logging
import pprint
from pathlib import Path

from ekfsm.system import System

config = Path(__file__).parent / "zip2-ccu-only.yaml"
system = System(config)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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

ccu = system[1]
ccu.print()
print(f"probing CCU: {ccu.probe()}")

eeprom = ccu.mux.ch00.eeprom

eeprom.write_cserial(12345678)
assert eeprom.cserial() == 12345678

eeprom.write_cmodel("SRS-C001")
assert eeprom.cmodel() == "SRS-C001"

eeprom.write_cvendor("EKF Elektronik")
assert eeprom.cvendor() == "EKF Elektronik"

eeprom.write_crevision("2.0")
assert eeprom.crevision() == "2.0"

eeprom.write_unit(1)
assert eeprom.unit() == 1
