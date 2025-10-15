from typing import Callable, Optional
from ekfsm.core.components import HWModule
from ekfsm.devices.generic import Device
from ekfsm.log import ekfsm_logger
import io4edge_client.core.coreclient as Client

from re import sub

logger = ekfsm_logger(__name__)


class IO4Edge(Device):
    """
    Device class for handling IO4Edge devices.
    """

    def __init__(
        self,
        name: str,
        parent: HWModule | None = None,
        children: list[Device] | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        logger.debug(f"Initializing IO4Edge device '{name}'")

        super().__init__(name, parent, children, abort, *args, **kwargs)

        attr = self.hw_module.slot.attributes
        if (
            attr is None
            or not hasattr(attr, "slot_coding")
            or getattr(attr, "slot_coding") is None
        ):
            logger.error(
                f"Slot attributes for {self.hw_module.slot.name} are not set or do not contain 'slot_coding'"
            )
            raise ValueError(
                f"Slot attributes for {self.hw_module.slot.name} are not set or do not contain 'slot_coding'."
            )
        else:
            geoaddr = int(attr.slot_coding)
            self._geoaddr = geoaddr
            logger.debug(f"IO4Edge '{name}' geo address: {geoaddr}")

        _, module_name = sub(r"-.*$", "", self.hw_module.board_type).split(maxsplit=1)
        self._module_name = module_name
        logger.debug(f"IO4Edge '{name}' module name: {module_name}")

        try:
            self.client = Client.new_core_client(self.deviceId)
            logger.info(f"IO4Edge '{name}' initialized with device ID: {self.deviceId}")
        except Exception as e:
            logger.error(f"Failed to create IO4Edge core client for '{name}': {e}")
            raise

    @property
    def deviceId(self) -> str:
        """
        Returns the device ID for the IO4Edge device.
        The device ID is a combination of the module name and the geo address.
        """
        return f"{self._module_name}-geo_addr{self._geoaddr:02d}"

    def identify_firmware(self) -> tuple[str, str]:
        response = self.client.identify_firmware()
        return (
            response.title,
            response.version,
        )

    def load_firmware(
        self, cfg: bytes, progress_callback: Optional[Callable[[float], None]] = None
    ) -> None:
        """
        Load firmware onto the IO4Edge device.

        cfg
            Firmware configuration bytes.
        progress_callback
            Optional callback for progress updates.
        """
        self.client.load_firmware(cfg, progress_callback)

    def restart(self) -> None:
        self.client.restart()

    def load_parameter(self, name: str, value: str) -> None:
        """
        Set a parameter onto the IO4Edge device.

        cfg
            The name of the parameter to load.
        value
            The value to set for the parameter.
        """
        self.client.set_persistent_parameter(name, value)

    def get_parameter(self, name: str) -> str:
        """
        Get a parameter value from the IO4Edge device.

        Returns
            The value of the requested parameter.
        """
        return self.client.get_persistent_parameter(name)

    def __repr__(self):
        return f"{self.name}; DeviceId: {self.deviceId}"
