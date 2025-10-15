import logging
import pprint
from pathlib import Path

import pytest
import yaml

from ekfsm.core.utils import module_schema


def test_module_schema():
    boards_path = Path(__file__).parent.parent / "ekfsm" / "boards" / "oem" / "ekf"

    for module_path in boards_path.glob("*.yaml"):
        pprint.pprint(f"Module: {module_path}")

        with open(module_path) as file:
            yaml_data = yaml.safe_load(file)
            module_schema.validate(yaml_data)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    pytest.main([__file__])
