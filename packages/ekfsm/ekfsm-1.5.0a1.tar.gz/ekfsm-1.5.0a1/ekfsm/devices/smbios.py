from pathlib import Path

from ekfsm.core.components import HWModule
from ekfsm.core.sysfs import SysfsDevice, sysfs_root
from ekfsm.log import ekfsm_logger

from .generic import Device

logger = ekfsm_logger(__name__)


class SMBIOS(Device):
    """
    A class to represent the SMBIOS device.

    A SMBIOS device is a virtual device that is used to read system
    configuration values from the DMI table.

    Note:
    Currently, only the board version / revision is read from the DMI table.
    """

    def __init__(
        self,
        name: str,
        parent: HWModule | None = None,
        children: list["Device"] | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        logger.debug(f"Initializing SMBIOS device '{name}'")

        try:
            dmi_path = sysfs_root() / Path("devices/virtual/dmi/id")
            self.sysfs_device: SysfsDevice | None = SysfsDevice(dmi_path, False)
            logger.info(f"SMBIOS '{name}' initialized with DMI table at {dmi_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SMBIOS '{name}' with DMI table: {e}")
            raise

        super().__init__(name, parent, None, abort, *args, **kwargs)

    def revision(self) -> str:
        """
        Get the board revision from the DMI table.

        Returns
        -------
        str
            The board revision.
        """
        logger.debug(f"Reading board revision for SMBIOS '{self.name}'")
        try:
            revision = self.sysfs.read_utf8("board_version")
            logger.debug(f"SMBIOS '{self.name}' board revision: {revision}")
            return revision
        except Exception as e:
            logger.error(f"Failed to read board revision for SMBIOS '{self.name}': {e}")
            raise
