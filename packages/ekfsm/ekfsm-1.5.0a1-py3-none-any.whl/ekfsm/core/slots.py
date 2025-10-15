from enum import Enum
from typing import Any

from munch import Munch

from ekfsm.core.components import HWModule


class SlotType(Enum):
    """
    Define the types of slots that can be found in a chassis.

    The following slot types are defined:
    - CPCI_S0_UTILITY: CompactPCI Serial Utility Connector
    - CPCI_S0_SYS: CompactPCI Serial System Slot
    - CPCI_S0_PER: CompactPCI Serial Peripheral Slot
    - CPCI_S0_PSU: CompactPCI Serial Power Supply Slot
    """

    CPCI_S0_UTILITY = 1  # CompactPCI Serial Utility Connector
    CPCI_S0_SYS = 2  # CompactPCI Serial System Slot
    CPCI_S0_PER = 3  # CompactPCI Serial Peripheral Slot
    CPCI_S0_PSU = 4  # CompactPCI Serial Power Supply Slot

    @classmethod
    def from_string(cls, name: str) -> "SlotType":
        try:
            return cls[name]
        except KeyError:
            raise ValueError(f"Invalid {cls.__name__}: {name}")

    def to_string(self) -> str:
        return self.name


class Slot:
    """
    A slot represents a physical slot in a chassis.

    Parameters
    ----------
    name
        The name of the slot, e.g. "SlotA" or "CPCI-SYSTEMSLOT"
    slot_type
        The type of the slot, e.g. SlotType.CPCI_S0_SYS
    desired_hwmodule_type
        The desired type of the hardware module that should be in the slot (currently unused)
    desired_hwmodule_name
        The name to be used for the hardware module instance in the slot. (currently unused)
    master
        The master board of the system
    hwmodule
        The hardware module that is in the slot
    number
        The number of the slot
    attributes
        Additional attributes
    """

    def __init__(
        self,
        name: str,
        slot_type: SlotType,
        desired_hwmodule_type: str,
        desired_hwmodule_name: str,
        number: int,
        hwmodule: HWModule | None = None,
        master: HWModule | None = None,
        attributes: Munch | None = None,
    ) -> None:
        self._name = name
        self.slot_type = slot_type
        self._desired_hwmodule_type = desired_hwmodule_type
        self._desired_hwmodule_name = desired_hwmodule_name
        self.number = number
        self.hwmodule = hwmodule
        self.master = master
        self.attributes = attributes

    def info(self) -> dict[str, Any]:
        """
        Returns a dictionary with information about the slot.

        - name (str): The name of the slot
        - slot_type (str): The type of the slot
        - number (int): The number of the slot
        - desired_hwmodule_type (str): The desired type of the hardware module
        - actual_hwmodule_type (str): The actual type of the hardware module
        - desired_hwmodule_name (str): The desired name of the hardware module
        - is_populated (bool): Is the slot populated?
        - is_correctly_populated (bool): Is the slot correctly populated?
        """
        return {
            "name": self._name,
            "slot_type": self.slot_type.to_string(),
            "number": self.number,
            "desired_hwmodule_type": self._desired_hwmodule_type,
            "actual_hwmodule_type": self.hwmodule.board_type if self.hwmodule else None,
            "desired_hwmodule_name": self._desired_hwmodule_name,
            "is_populated": self.is_populated,
            "is_correctly_populated": self.is_correctly_populated,
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self._name}, slot_type={self.slot_type})"
        )

    @property
    def name(self) -> str:
        """
        Return the name of the slot.
        """
        return self._name

    @property
    def is_populated(self) -> bool:
        """
        Return True if the slot is populated, False otherwise.
        """
        return self.hwmodule is not None

    @property
    def is_correctly_populated(self) -> bool:
        """
        Return True if the slot is populated with the desired hardware module type, False otherwise.
        """
        return (
            self.hwmodule is not None
            and self.hwmodule.board_type.lower() == self._desired_hwmodule_type.lower()
        )


class Slots(Munch):
    """
    A collection of slots.

    Slots are stored in a dictionary-like object, where the key is the slot name and the value is the Slot object.
    Slots can be accessed by name, by number or via an attribute access matching the key.

    Example
    -------
    >>> from ekfsm..core.slots import Slot, Slots, SlotType
    >>> slotA = Slot("SlotA", SlotType.CPCI_S0_PER, "Bla", "Blubb", 3)
    >>> slots = Slots((slotA.name, slotA))
    >>> print(slots[name])
    >>> print(slots.slotA) # attribute access, same as slots[name]
    >>> print(slots[3]) # number access, same as slots.slotA
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __getitem__(self, key: int | str) -> Slot:
        """
        Get a slot by name, number or attribute access.
        """
        if isinstance(key, int):
            return next(slot for slot in self.values() if slot.number == key)

        return super().__getitem__(key)

    def __setitem__(self, key, value):
        """
        Add a Slot object to the collection.

        Raises
        ------
        ValueError
            if:
            - the value is not a Slot object
            - the key does not match the slot name
            - the slot already exists in collection
            - or the slot number is not unique
        """
        if not isinstance(value, Slot):
            raise ValueError("Only Slot instances can be added to a Slots collection.")
        elif key != value.name:
            raise ValueError("Slot name must match key.")
        elif value in self.values():
            raise ValueError("Slot already exists in collection.")
        elif value.number in [slot.number for slot in self.values()]:
            raise ValueError("Slot number must be unique.")

        return super().__setitem__(key, value)

    def add(self, slot: Slot) -> None:
        """
        Add a Slot object to the collection, where the name of the slot object is used as the key.

        Example
        -------
        >>> from ekfsm.core.slots import Slot, Slots, SlotType
        >>> slotA = Slot("SlotA", SlotType.CPCI_S0_PER, "Bla", "Blubb", 3)
        >>> slots = Slots()
        >>> slots.add(slotA) # add slotA to the collection
        >>> print(slots.SlotA) # attribute access, same as slots["SlotA"]
        """
        self[slot.name] = slot
