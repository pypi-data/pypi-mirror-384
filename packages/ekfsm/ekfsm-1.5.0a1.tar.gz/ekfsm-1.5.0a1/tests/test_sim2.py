# Test with config file that doesn't match the sysfs entries
import logging
import pprint
from pathlib import Path

import pytest

from ekfsm.simctrl import enable_simulation, register_gpio_simulations
from ekfsm.system import HWModule, System


@pytest.fixture
def simulation():
    enable_simulation(Path(__file__).parent / "sim" / "sys")
    register_gpio_simulations()


def test_system(simulation):
    config = Path(__file__).parent / "sim" / "test_system_inconsistent.yaml"
    system = System(config)
    pprint.pprint(f"System slots {system.slots}")

    psu = system.psu
    assert psu is not None
    assert isinstance(psu, HWModule)
    assert psu.probe()
    assert psu.inventory.vendor() == "Hitron"
    assert psu.inventory.model() == "HDRC300S-110J-D120E(N)"
    assert psu.main.voltage() == 12.2
    assert psu.sby.current() == 0.5
    slot_info = system.slots.PSU_SLOT.info()
    assert slot_info["is_populated"] is True
    assert slot_info["is_correctly_populated"] is False  # as no desired HWModule type in config

    cpu = system["CPU"]
    assert cpu is not None
    assert isinstance(cpu, HWModule)
    assert cpu.inventory.vendor() == "EKF Elektronik"
    assert cpu.inventory.model() == "SC9-TOCCATA"
    assert cpu.inventory.serial() == "53082029"

    cpu_slot_info = system.slots.SYSTEM_SLOT.info()
    assert cpu_slot_info["name"] == "SYSTEM_SLOT"
    assert cpu_slot_info["is_populated"] is True
    assert cpu_slot_info["is_correctly_populated"] is True

    # sysfs entries are for SRF-FAN, but config file says SUR-LED, so SUR specific devices are not found
    sur = system.slots["SLOT1"].hwmodule
    assert sur is not None
    assert isinstance(sur, HWModule)
    assert sur.board_type == "EKF SRF-FAN"
    assert sur.inventory.vendor() == "EKF Elektronik"
    assert sur.inventory.model() == "SRF-FAN"

    sur_slot = system.slots.SLOT1
    slot_info = sur_slot.info()
    assert slot_info["name"] == "SLOT1"
    assert slot_info["is_populated"] is True
    assert slot_info["is_correctly_populated"] is False
    assert slot_info["actual_hwmodule_type"] == "EKF SRF-FAN"

    slot_info = system.slots.SLOT2.info()
    assert slot_info["name"] == "SLOT2"
    assert slot_info["is_populated"] is False
    assert slot_info["is_correctly_populated"] is False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # pytest.main([__file__,"--capture=tee-sys"])
    pytest.main([__file__])
