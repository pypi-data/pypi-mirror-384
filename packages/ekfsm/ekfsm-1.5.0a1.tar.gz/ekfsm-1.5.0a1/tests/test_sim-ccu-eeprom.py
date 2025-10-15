import logging
from pathlib import Path

import pytest

from ekfsm.simctrl import enable_simulation, register_gpio_simulations
from ekfsm.system import System


@pytest.fixture
def simulation():
    enable_simulation(Path(__file__).parent / "sim" / "sys")
    register_gpio_simulations()


def test_system(simulation):
    config = Path(__file__).parent / "sim" / "test_system.yaml"
    system = System(config, abort=True)

    ccu = system.ccu
    assert ccu is not None

    eeprom = ccu.mux.ch00.eeprom

    eeprom.write_cmodel("SRS-C001")
    assert eeprom.cmodel() == "SRS-C001"

    eeprom.write_cvendor("EKF Elektronik")
    assert eeprom.cvendor() == "EKF Elektronik"

    eeprom.write_crevision("2.0")
    assert eeprom.crevision() == "2.0"

    eeprom.write_unit(1)
    assert eeprom.unit() == 1

    data = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"
    ccu.custom_eeprom.write(data)
    assert ccu.custom_eeprom.read()[0 : len(data)] == data


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    pytest.main([__file__])
