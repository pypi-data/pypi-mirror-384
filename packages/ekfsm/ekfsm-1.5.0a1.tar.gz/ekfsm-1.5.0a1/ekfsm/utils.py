from pathlib import Path
from typing import Generator

_CFG_DIR = Path(__file__).parent / "boards"


def find_board_config(module_type: str) -> Path | None:
    """
    Find a matching board config in `boards/oem/` given the module type specified in
    the system configuration file.

    Parameters
    ----------
    module_type
        Board type specified in the system configuration for a slot.
        It must consist of an OEM and the board type, separated by whitespace. Neither
        part may contain any other whitespace.
    """
    oem, board = module_type.split(maxsplit=1)
    if (path := _CFG_DIR / "oem" / oem.strip().lower() / f"{board.strip().lower()}.yaml").exists():
        return path
    return None


def all_board_cfg_files() -> Generator[Path, None, None]:
    """
    Generator that recursively yields all *.yaml files in the config directory.

    Yields
    ------
    item: Path
        Path to a config file.
    """
    path = Path(_CFG_DIR)
    for item in path.rglob("*.yaml"):
        if item.is_file():
            yield item


def next_or_raise(it, exc):
    value = next(it, None)
    if value is None:
        raise exc
    return value
