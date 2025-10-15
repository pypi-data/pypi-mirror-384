from pathlib import Path
from typing import Any, Tuple

import yaml
from munch import Munch, munchify

from ekfsm.core.components import SysTree
from ekfsm.utils import all_board_cfg_files, find_board_config

from .config import load_config
from .core import HWModule
from .core.slots import Slot, Slots, SlotType
from .exceptions import ConfigError
from .log import ekfsm_logger


class System(SysTree):
    """
    A System represents a CPCI system.

    Once initialised, it will create:
        - a list of boards that are present in the system which can be accessed either by name or by slot number.
        - a list of slots that are present in the system which can be accessed under the slots attribute.

    Visual representation of the system is shown as trees of HW Modules and attached devices.

    Attributes
    ----------
    name
        The name of the system.
    slots
        A dictionary-like object that contains all slots in the system.
    boards
        A list of all boards in the system.
    master
        The master board of the system.
    master_slot_number
        The slot number of the master board.
    config
        The system configuration.


    Accessing boards
    ----------------

    Iterating over the system will iterate over all boards in the system.

    <board_name>
        The board object can be accessed by its name.
    <slot_number>
        The board object can be accessed by its slot number.


    Example
    -------
    >>> from ekfsm.system import System
    >>> system = System("path/to/config.yaml")
    >>> print(system) # Print the system configuration as trees of HWModules
    >>> system.print() # same as above
    >>> cpu = system.cpu # Access the CPU board by its name
    >>> cpu = system[0] # Access the CPU board by its slot index (index as in configuration file)
    >>> print(system.slots) # Print all slots in the system
    >>> print(system.boards) # Print all boards in the system
    >>> for b in system: # Iterate over all boards in the system
    >>>    print(b.name + b.slot.name) # Print the name of the board and the slot it is in
    """

    def __init__(self, config: Path, abort: bool = False) -> None:
        """
        Parameters
        ----------
        config
            Path to the config that specifies the system and how the slots are filled.
        abort
            If True, abort the program if a board cannot be created. If False, leave the slot empty.
            Default is False.
        """
        self.config_path = config
        self.config = load_config(str(self.config_path))
        self.name = self.config.system_config.name

        super().__init__(self.name, abort=abort)

        self.logger = ekfsm_logger(__name__)
        self._init_system(config)
        self._init_slot_attrs()
        self._aggregate_provider_functions()
        self.children = self.boards

    def _init_system(self, config: Path):
        self.slots: Slots = Slots()
        self.boards: list[HWModule] = []

        self.master, self.master_slot_number = self._create_master()
        if self.master is None:
            raise ConfigError("No master board found in system configuration!")

        self.logger.info(f"Master board found in slot {self.master_slot_number}")

        for i, slot_cfg in enumerate(self.config.system_config.slots):
            hwmod: HWModule | Slot | None
            if i == self.master_slot_number:
                hwmod = self.master
            else:
                hwmod, slot = self.create_hwmodule(slot_cfg, i, self.master)

            if hwmod is not None:
                hwmod.slot.hwmodule = hwmod
                self.boards.append(hwmod)
                self.slots.add(hwmod.slot)
            else:
                self.slots.add(slot)

    def _init_slot_attrs(self):
        for board in self.boards:
            setattr(self, board.instance_name.lower(), board)

    def _aggregate_provider_functions(self):
        if hasattr(self.config.system_config, "aggregates"):
            agg = self.config.system_config.aggregates
            if agg is not None:
                for key, value in agg.items():
                    prv = Munch()
                    for board in self.boards:
                        if hasattr(board, key):
                            prv.update({value: getattr(board, key)})
                    if value in prv.keys():
                        setattr(self, value, prv[value])

    def reload(self):
        """
        Reload the current system configuration.

        Important
        ---------
        This will rebuild all system objects and reinitialize the system tree.
        """
        self.__init__(self.config_path)

    def _create_master(self) -> Tuple[HWModule | None, int]:
        for i, slot in enumerate(self.config.system_config.slots):
            if "attributes" in slot:
                if "is_master" in slot.attributes:
                    if slot.attributes.is_master:
                        master, _ = self.create_hwmodule(slot, i, None)
                        if master is not None:
                            master.master = master  # ???
                            return master, i
                        else:
                            return None, -1
        return None, -1  # ???

    def create_hwmodule(
        self, slot_entry: Munch, slot_number: int, master: HWModule | None
    ) -> Tuple[HWModule | None, Slot]:
        """
        Create HWModule object for the slot.

        Parameters
        ----------
            slot_entry
                The slot entry config (usually part of the system configuration).
            slot_number
                The slot number of the slot.
            master
                The master board of the system.

        Returns
        -------
            HWModule and Slot. HWodule is None if it cannot be created.
        """
        slot = self._create_slot(slot_entry, slot_number, master)
        board_type = slot_entry.desired_hwmodule_type
        board_name = slot_entry.desired_hwmodule_name

        self.logger.debug(
            f"Creating HWModule {board_type} (desired name: {board_name}) in slot {slot.name}"
        )

        if board_type != "":
            # try to create first the desired board
            path = find_board_config(board_type)
            if path is None:
                self.logger.error(
                    f"No board config found for {board_type} (desired name: {board_name})"
                )
                return None, slot

            try:
                hwmod = self._create_hwmodule_from_cfg_file(slot, board_name, path)

            except Exception as e:
                if self.abort:
                    self.logger.error(
                        f"failed to create desired HWModule {board_type} (as {board_name}): {e}. Aborting!"
                    )
                    raise e
                else:
                    self.logger.error(
                        f"failed to create desired HWModule {board_type} (as {board_name}): {e}. Leaving slot empty!"
                    )
                    return None, slot

            # try to probe desired board type
            if hwmod.probe():
                self.logger.info(
                    f"Found desired board type {hwmod.board_type} for slot {slot.name}"
                )
                return hwmod, slot

        # try all other boards types. Maybe someone inserted the wrong board
        self.logger.info(
            f"Probing failed. Trying all other board types for slot {slot.name}"
        )
        for path in all_board_cfg_files():
            try:
                hwmod = self._create_hwmodule_from_cfg_file(slot, board_name, path)
            except ConfigError:
                # slot type not matching, ignore
                # ??? should we log this?
                continue
            except Exception as e:
                self.logger.debug(
                    f"failed to create HWmodule {path} for slot {slot.name}: {e}"
                )
                continue

            if hwmod.probe():
                self.logger.info(
                    f"Found other board type {hwmod.board_type} for slot {slot.name}"
                )
                return hwmod, slot

        return None, slot

    def _create_slot(
        self, slot_entry: Munch, slot_number: int, master: HWModule | None
    ) -> Slot:
        attributes = None
        if "attributes" in slot_entry:
            attributes = slot_entry.attributes

        return Slot(
            slot_entry.name,
            SlotType.from_string(slot_entry.slot_type),
            slot_entry.desired_hwmodule_type,
            slot_entry.desired_hwmodule_name,
            slot_number,
            None,
            master,
            attributes,
        )

    def _create_hwmodule_from_cfg_file(
        self, slot: Slot, board_name: str, path: Path
    ) -> HWModule:
        """
        Try to create a HWModule object from a board config file.
        It does not probe the hardware.

        Returns
        -------
            HWModule object.

        Raises
        ------
            FileNotFoundError
                If the board config file does not exist.
            ConfigError
                If the slot type in the config file does not match the slot type.
            Exception
                If something else went wrong.
        """

        with open(path) as file:
            yaml_data = yaml.safe_load(file)
            cfg = munchify(yaml_data)
            # only instantiate if slot type matches
            if cfg.slot_type != slot.slot_type.to_string():
                raise ConfigError(
                    f"Slot type mismatch for slot {slot.name}: {cfg.slot_type} != {slot.slot_type}"
                )

            hwmod = HWModule(
                instance_name=board_name,
                config=yaml_data,
                slot=slot,
                abort=self.abort,
                parent=self,
            )

            return hwmod

    def get_module_in_slot(self, idx: int) -> HWModule | None:
        """
        Get the HWModule in the given slot.

        Parameters
        ----------
            idx
                The slot index.
        Returns
        -------
            HWModule
                The HWModule in the given slot.
            None
                If no HWModule is present in the given slot.
        """
        return next(
            (
                v.hwmodule
                for k, v in self.slots.items()
                if getattr(v, "number", None) == idx
            ),
            None,
        )

    def get_module_by_name(self, name: str) -> HWModule | None:
        """
        Get the HWModule by its name.

        Parameters
        ----------
            name
                The name of the HWModule.

        Returns
        -------
            HWModule
                The HWModule with the given name.
            None
                If no HWModule is present with the given name.
        """
        return next(
            (
                b
                for b in self.boards
                if getattr(b, "instance_name", None) is not None
                and getattr(b, "instance_name").lower() == name.lower()
            ),
            None,
        )

    def __iter__(self):
        return iter(self.boards)

    def __getitem__(self, key) -> HWModule:
        if isinstance(key, int):
            value = self.get_module_in_slot(key)
        else:
            value = self.get_module_by_name(key)

        if value is None:
            raise KeyError(f"Board {key} not found in system!")

        return value

    def __getattr__(self, name: str) -> Any:
        """Access board by attribute using dot notation"""
        # This fixes mypy error: "... has no object ..."
        if (hw_module := self.get_module_by_name(name)) is not None:
            return hw_module

        raise AttributeError(
            f"'{type(self).__name__}' object has no board with name '{name}'"
        )

    def __repr__(self):
        return f"System (name={self.name})"
