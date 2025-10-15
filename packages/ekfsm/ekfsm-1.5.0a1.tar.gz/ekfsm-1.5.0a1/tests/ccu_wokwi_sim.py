import logging
import time
from pathlib import Path

from ekfsm.simctrl import SocketSmbus, enable_simulation, register_gpio_simulations, register_smbus_sim
from ekfsm.system import System

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

enable_simulation(Path(__file__).parent / "sim" / "sys")

# redirecting smbus to socket running in wokwi, where the ESP32 is simulating the smbus via socket
register_smbus_sim(15, 0x28, SocketSmbus("172.28.64.1", 10000))

register_gpio_simulations()

config = Path(__file__).parent / "sim" / "test_system.yaml"
system = System(config)

ccu = system.ccu
ccu.print()

print(f"CCU firmware: {ccu.management.identify_firmware()}")


# def progress_callback(offset):
#     print(f"Loading firmware: {offset}")

# with open("/home/klaus/winDownloads/fw-ccu-00-default.bin", "rb") as f:
#     firmware = f.read()
#     ccu.management.load_firmware(firmware, progress_callback)


params = """
{
    "version": "1.0",
    "parameters": {
        "fan-defrpm":   "4500",
        "shutdn-delay": "40"
    }
}
"""
ccu.management.load_parameterset(params)

print(f"CCU parameters: {ccu.management.get_parameterset()}")

print(f"CCU temperature: {ccu.th.temperature()}C")
print(f"CCU humidity: {ccu.th.humidity()}%")
print(f"CCU VIN voltage: {ccu.vin.voltage()}V")

ccu.fan.push_temperature(-1, 30.0)
for i in range(7):
    for fan in range(2):
        print(f"CCU fan {fan} status: {ccu.fan.fan_status(fan)}")
    time.sleep(1)
