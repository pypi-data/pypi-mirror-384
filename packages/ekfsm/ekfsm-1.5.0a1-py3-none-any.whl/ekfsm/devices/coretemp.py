from __future__ import annotations

import glob
import os
from pathlib import Path

import ekfsm.core
from ekfsm.core.sysfs import sysfs_root
from ekfsm.devices.generic import Device
from ekfsm.log import ekfsm_logger

logger = ekfsm_logger(__name__)

# Path to the root of the HWMON sysfs filesystem
HWMON_ROOT = sysfs_root() / Path("class/hwmon")


def find_core_temp_dir(hwmon_dir) -> Path:
    """
    Find the directory containing the coretemp hwmon device.

    Args:
        hwmon_dir: Path to the hwmon directory

    Returns:
        Path to the directory containing the coretemp hwmon device

    Raises:
        FileNotFoundError: If no coretemp directory is found
    """
    # List all 'name' files in each subdirectory of hwmon_dir
    name_files = glob.glob(os.path.join(hwmon_dir, "*", "name"))

    # Search for the file containing "coretemp"
    for name_file in name_files:
        with open(name_file, "r") as file:
            if file.readline().strip() == "coretemp":
                # Return the directory containing this file
                return Path(os.path.dirname(name_file))

    raise FileNotFoundError("No coretemp directory found")


class CoreTemp(Device):
    """
    This class provides an interface to read the CPU core temperature from the HWMON device.

    Note:
    Currently, only the average temperature over all cores is read from the HWMON device.
    """

    def __init__(
        self,
        name: str,
        parent: Device,
        children: list["Device"] | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        logger.debug(f"Initializing CoreTemp device '{name}'")

        try:
            dir = find_core_temp_dir(sysfs_root() / Path("class/hwmon"))
            logger.debug(f"Found coretemp directory: {dir}")
            self.sysfs_device = ekfsm.core.sysfs.SysfsDevice(dir, False)
            logger.info(f"CoreTemp '{name}' initialized with sysfs device at {dir}")
        except FileNotFoundError as e:
            logger.error(f"Failed to initialize CoreTemp '{name}': {e}")
            raise

        super().__init__(name, parent, None, abort, *args, **kwargs)

    def cputemp(self):
        """
        Get the CPU temperature from the HWMON device.

        Returns
        -------
        int
            The CPU temperature in degrees Celsius.
        """
        logger.debug(f"Reading CPU temperature for CoreTemp '{self.name}'")
        try:
            temp_raw = self.sysfs.read_float("temp1_input")
            temp_celsius = temp_raw / 1000
            logger.debug(
                f"CoreTemp '{self.name}' raw reading: {temp_raw}, temperature: {temp_celsius}°C"
            )
            return temp_celsius
        except Exception as e:
            logger.error(
                f"Failed to read CPU temperature for CoreTemp '{self.name}': {e}"
            )
            raise
