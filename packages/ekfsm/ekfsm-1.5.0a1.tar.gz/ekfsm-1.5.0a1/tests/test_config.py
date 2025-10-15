import munch

from ekfsm.config import load_config


def test_config():
    config = load_config("tests/data/cfg_simple.yaml")
    assert isinstance(config, munch.Munch)

    assert config.system_config.name == "Simple System"
    assert len(config.system_config.slots) == 2
    assert config.system_config.slots[0].name == "SLOT1"
    assert config.system_config.slots[0].slot_type == "CPCI_S0_SYS"
    assert config.system_config.slots[0].desired_hwmodule_type == "EKF SC9"
    assert config.system_config.slots[0].desired_hwmodule_name == "CPU1"
    assert not hasattr(config.system_config.slots[0], "attributes")

    assert config.system_config.slots[1].name == "SLOT7"
    assert config.system_config.slots[1].slot_type == "CPCI_S0_PER"
    assert config.system_config.slots[1].desired_hwmodule_type == "EKF SUR"
    assert config.system_config.slots[1].desired_hwmodule_name == "SER1"
    attr = config.system_config.slots[1].attributes
    assert attr.slot_coding == 0
