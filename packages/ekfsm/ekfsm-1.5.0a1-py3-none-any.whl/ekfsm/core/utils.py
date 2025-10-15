from __future__ import annotations

import logging
from pprint import pformat
from typing import TYPE_CHECKING, Any

from schema import Optional, Or, Schema, SchemaError, Use
from termcolor import colored

from ekfsm.devices import CLASS_MAP
from ekfsm.exceptions import ConfigError

if TYPE_CHECKING:
    from ekfsm.devices.generic import Device

    from .components import HWModule


def import_board(logger: logging.Logger, data, parent=None, abort: bool = False):
    from .components import HWModule

    device_type = data.get("device_type")
    nodecls = CLASS_MAP.get(device_type)
    if nodecls is None:
        raise ConfigError(f"Unknown device type: {device_type}")

    children = data.pop("children", [])
    if parent is not None and isinstance(parent, HWModule):
        # ???
        pass

    if provides := data.get("provides"):
        for p in provides:
            interfaces = data["provides"][p]

            for interface in interfaces:
                if isinstance(interface, str):
                    if attr := getattr(nodecls, interface, None):
                        if not callable(attr) and not abort:
                            raise ConfigError("No such method")
                elif isinstance(interface, dict):
                    for key, value in interface.items():
                        if attr := getattr(nodecls, value, None):
                            if not callable(attr) and not abort:
                                raise ConfigError("No such method")
                else:
                    raise ConfigError("Error in board configuration")

    node = nodecls(parent=parent, abort=abort, **data)

    if children is not None:
        for child in children:
            try:
                logger.debug(f"Importing sub device {pformat(child)}")
                import_board(logger, data=child, parent=node, abort=abort)
            except Exception as e:
                if abort:
                    logger.error(
                        f"Failed to import sub device {pformat(child)}: {e}. Aborting."
                    )
                    raise e
                else:
                    logger.error(
                        f"Failed to import sub device {pformat(child)}: {e}. Continuing anyway."
                    )
    return node


def provides_validator(x: Any) -> Any:
    if isinstance(x, str):
        return x
    elif isinstance(x, dict) and len(x) == 1:
        key, value = next(iter(x.items()))
        if isinstance(key, str) and isinstance(value, str):
            return x
    raise SchemaError(
        "Each provides item must be either a string or a dictionary with one string key/value pair"
    )


device_schema = Schema({})

_device_structure = Schema(
    {
        "device_type": str,
        "name": str,
        Optional("addr"): int,
        Optional("slot_coding_mask"): int,
        Optional("channel_id"): int,
        Optional("service_suffix"): str,
        Optional("keepaliveInterval"): int,
        Optional("provides"): {
            Optional(str): [Use(provides_validator)],
        },
        Optional("children"): Or(None, [device_schema]),
    }
)

device_schema._schema = _device_structure

module_schema = Schema(
    {
        "id": Or(int, str),
        "name": str,
        "slot_type": str,
        Optional("children"): [device_schema],
        Optional("bus_masters"): {
            Optional("i2c"): dict,
        },
    }
)


def deserialize_module(logger: logging.Logger, data: dict) -> tuple[str, str, str]:
    """
    docstring
    """
    module_schema.validate(data)

    id, name, slot_type = (data[key] for key in ["id", "name", "slot_type"])
    logger.debug(colored(f"Importing top level module {pformat(name)}", "green"))

    return id, name, slot_type


def deserialize_hardware_tree(
    logger: logging.Logger, data: dict, parent: "HWModule"
) -> list["Device"]:
    abort = parent.abort

    module_schema.validate(data)

    children = data.pop("children", None)
    if not children:
        return []

    devices = []
    for child in children:
        try:
            logger.debug(
                colored(f"Importing top level device {pformat(child)}", "green")
            )

            node = import_board(logger, child, parent=parent, abort=abort)
            devices.append(node)
        except Exception as e:
            logger.error(
                colored(
                    f"Failed to import top-level device {pformat(child)}: {e}", "red"
                )
            )
            logger.error(colored("Aborting." if abort else "Continuing anyway", "red"))
            if abort:
                raise

    return devices
