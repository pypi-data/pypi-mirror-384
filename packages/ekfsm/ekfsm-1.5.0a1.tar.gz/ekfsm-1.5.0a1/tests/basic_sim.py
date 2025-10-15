import logging
import pprint
from pathlib import Path

from ekfsm.simctrl import enable_simulation, register_gpio_simulations
from ekfsm.system import System

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

enable_simulation(Path(__file__).parent / "sim" / "sys")
register_gpio_simulations()

config = Path(__file__).parent / "sim" / "test_system.yaml"
system = System(config, abort=True)
system.print()

pprint.pprint(f"System slots {system.slots}")

cpu = system[1]
cpu.print()

print(f"CPU inventory: {cpu.inventory.vendor()} {cpu.inventory.model()} {cpu.inventory.serial()}")

srf = system["FAN"]
srf.print()

psu = system.psu
psu.print()

psu = system.slots["PSU_SLOT"].hwmodule
psu.print()

print(f"Slot info {system.slots['PSU_SLOT'].info()}")


print(f"PSU main: {psu.main.voltage()}V  {psu.main.current()}A")
print(f"PSU sby: {psu.sby.voltage()}V  {psu.sby.current()}A")
print(
    f"PSU inventory: {psu.inventory.vendor()} {psu.inventory.model()} {psu.inventory.revision()} {psu.inventory.serial()}"
)

print(f"SRF MUX bus num {srf.mux.get_i2c_bus_number()}")
print(f"SRF GPIO bus num {srf.mux.ch00.gpio.get_i2c_bus_number()}")
