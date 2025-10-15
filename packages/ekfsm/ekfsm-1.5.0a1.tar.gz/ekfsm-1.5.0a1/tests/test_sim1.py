import logging
import pprint
from pathlib import Path

import pytest

from ekfsm.devices.pmbus import PSUStatus
from ekfsm.simctrl import enable_simulation, register_gpio_simulations
from ekfsm.system import HWModule, System


@pytest.fixture
def simulation():
    enable_simulation(Path(__file__).parent / "sim" / "sys")
    register_gpio_simulations()


def test_system(simulation):
    config = Path(__file__).parent / "sim" / "test_system.yaml"
    system = System(config, abort=True)
    pprint.pprint(f"System slots {system.slots}")

    psu = system.psu
    assert psu is not None
    assert isinstance(psu, HWModule)
    assert psu.probe()
    assert psu.inventory.vendor() == "Hitron"
    assert psu.inventory.model() == "HDRC300S-110J-D120E(N)"
    assert psu.main.voltage() == 12.2
    assert psu.sby.current() == 0.5
    assert psu.th.temperature() == 22.0
    assert psu.main.status() == PSUStatus.OK
    assert psu.sby.status() == PSUStatus.OK

    cpu = system["CPU"]
    assert cpu is not None
    assert isinstance(cpu, HWModule)
    assert cpu.inventory.vendor() == "EKF Elektronik"
    assert cpu.inventory.model() == "SC9-TOCCATA"
    assert cpu.inventory.serial() == "53082029"

    srf = system.slots["SLOT1"].hwmodule
    assert srf is not None
    assert isinstance(srf, HWModule)

    assert srf.probe()

    assert srf.inventory.vendor() == "EKF Elektronik"
    assert srf.inventory.model() == "SRF-FAN"
    assert srf.inventory.revision() == "0"
    assert srf.inventory.serial() == "54021107"
    assert srf.mux.get_i2c_bus_number() == 1
    assert srf.mux.ch00.gpio.get_i2c_bus_number() == 9

    ccu = system.ccu
    assert ccu is not None
    version = ccu.mux.ch00.eeprom.version()
    assert version == 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    pytest.main([__file__])
