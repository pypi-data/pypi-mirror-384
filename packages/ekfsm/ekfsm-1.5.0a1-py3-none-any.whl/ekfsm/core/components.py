from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anytree import LevelGroupOrderIter, NodeMixin, RenderTree, findall
from munch import Munch

if TYPE_CHECKING:
    from ekfsm.devices.generic import Device

    from .slots import Slot


class SysTree(NodeMixin):
    """
    Base class for all system components including Hardware Modules and Devices.
    """

    def __init__(self, name: str, abort: bool = False) -> None:
        from ekfsm.log import ekfsm_logger

        self.logger = ekfsm_logger(name)
        self.name = name
        self.abort = abort

    def _render_tree(self) -> str:
        output = ""
        for pre, _, node in RenderTree(self):
            output += f"{pre}{repr(node)}" + "\n"
        return output

    def __str__(self):
        return self._render_tree()

    def print(self) -> None:
        print(self)


class HWModule(SysTree):
    """
    A HWModule represents an instantiation of a specifc hw board type,
    for example an instance of an EKF SC9 board.
    """

    def __init__(
        self,
        instance_name: str,
        config: dict,
        slot: Slot,
        abort: bool = False,
        *args,
        **kwargs,
    ) -> None:
        from ekfsm.core.utils import deserialize_hardware_tree, deserialize_module

        from .slots import SlotType

        super().__init__(instance_name, abort=abort)
        self._slot: Slot = slot
        self.config = config

        self.id, self.board_type, slot_type = deserialize_module(self.logger, config)
        self.children = deserialize_hardware_tree(self.logger, self.config, parent=self)

        self.slot_type = SlotType.from_string(slot_type)

        for children in LevelGroupOrderIter(self):
            for child in children:
                for sub_child in child.children:
                    setattr(child, sub_child.name.lower(), sub_child)

                    # If the device provides functions, add function and corresponding attributes to this hw module
                    self._create_functions_from_node_providers(sub_child)

    @property
    def is_master(self) -> bool:
        slot_attributes = self.slot.attributes
        if slot_attributes is not None and hasattr(slot_attributes, "is_master"):
            return slot_attributes.is_master
        return False

    def _create_functions_from_node_providers(self, device: Device) -> None:
        providers: Munch | None = getattr(device, "provides", None)

        if providers is not None:
            for key, value in providers.items():
                if key not in self.__dict__:
                    provider = Munch()
                else:
                    provider = getattr(self, key)

                provider.update(value)

                setattr(self, key, provider)

    def probe(self, *args, **kwargs) -> bool:
        from ekfsm.core.probe import ProbeableDevice

        nodes = findall(self, lambda node: isinstance(node, ProbeableDevice))
        for node in nodes:
            try:
                if node.probe(*args, **kwargs):
                    return True
            except Exception as e:
                self.logger.error(f"Error probing {node}: {e}")

        return False

    def info(self) -> dict[str, Any]:
        """
        Returns a dictionary with information about the hardware module.
        """
        return {
            "name": self.instance_name,
            "slot": self.slot,
        }

    @property
    def instance_name(self) -> str:
        if self.name is None:
            raise RuntimeError("Instance name not set")
        return self.name

    @property
    def slot(self) -> Slot:
        if self._slot is None:
            raise RuntimeError("Slot not set")
        return self._slot

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, type={self.board_type})"
