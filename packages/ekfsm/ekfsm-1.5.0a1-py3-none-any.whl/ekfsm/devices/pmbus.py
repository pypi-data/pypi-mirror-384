import re
from enum import IntFlag
from functools import wraps
from time import sleep

from ekfsm.core.components import SysTree
from ekfsm.exceptions import HWMonError
from ekfsm.log import ekfsm_logger

from ..core.probe import ProbeableDevice
from ..core.sysfs import list_sysfs_attributes, sysfs_root
from .generic import Device

__all__ = ["PSUStatus", "PMBus", "retry"]

logger = ekfsm_logger(__name__)


def retry(max_attempts=5, delay=0.5):
    """
    Retry decorator.

    Decorator that retries a function a number of times before giving up.

    This is useful for functions that may fail due to transient errors.

    Note
    ----
    This is needed for certain PMBus commands that may fail due to transient errors
    because page switching timing is not effectively handled by older kernel versions.

    Important
    ---------
    This decorator is _not_ thread-safe across multiple ekfsm processes. Unfortunately,
    we cannot use fcntl or flock syscalls with files on virtual filesystems like sysfs.

    Parameters
    ----------
    max_attempts
        The maximum number of attempts before giving up.
    delay
        The delay in seconds between attempts.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.exception(
                            f"Failed to execute {func.__name__} after {max_attempts} attempts: {e}"
                        )
                        raise e
                    logger.info(f"Retrying execution of {func.__name__} in {delay}s...")
                sleep(delay)

        return wrapper

    return decorator


class PSUStatus(IntFlag):
    """
    Represents the status of a PSU according to STATUS_BYTE register.

    See also
    --------
    External Documentation:
    `PMBus Power System Management Protocol Specification - Part II - Revision 1.4, Fig. 60 <https://pmbus.org/>`_

    Example
    -------
    >>> from ekfsm.devices.pmbus import PsuStatus
    >>> status = PsuStatus(0x1F)
    >>> status
    <PsuStatus.OUTPUT_OVERCURRENT|INPUT_UNDERVOLTAGE|TEMP_ANORMALY|COMMUNICATION_ERROR|ERROR: 31>
    >>> PsuStatus.OUTPUT_OVERCURRENT in status
    True
    >>> # OK is always present
    >>> PsuStatus.OK in status
    True
    >>> # Instead, check if status is OK
    >>> status == PsuStatus(0x00)
    False
    >>> PsuStatus.OUTPUT_OVERCURRENT in status
    False
    """

    OUTPUT_OVERVOLTAGE = 0x20
    OUTPUT_OVERCURRENT = 0x10
    INPUT_UNDERVOLTAGE = 0x08
    TEMP_ANORMALY = 0x04
    COMMUNICATION_ERROR = 0x02
    ERROR = 0x01
    OK = 0x00


logger = ekfsm_logger(__name__)


class PMBus(Device, ProbeableDevice):
    def __init__(
        self,
        name: str,
        parent: SysTree | None = None,
        children: list[Device] | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(name, parent, children, abort, *args, **kwargs)
        self.addr = self.get_i2c_chip_addr()
        self.sysfs_device = self.get_i2c_sysfs_device(self.addr, driver_required=True)

        try:
            for entry in self.sysfs_device.path.glob("hwmon/hwmon*"):
                if entry.is_dir():
                    attrs = list_sysfs_attributes(entry)
                    self.sysfs_device.extend_attributes(attrs)

                    debug_attrs_path = sysfs_root().joinpath(
                        f"kernel/debug/pmbus/{entry.name}"
                    )
                    debug_attrs = list_sysfs_attributes(debug_attrs_path)
                    self.sysfs_device.extend_attributes(debug_attrs)
        except FileNotFoundError:
            logger.debug("Expected sysfs attribute not found")
        except StopIteration:
            raise HWMonError("Device is not managed by hwmon subsystem")

    def probe(self, *args, **kwargs) -> bool:
        from ekfsm.core import HWModule

        assert isinstance(self.hw_module, HWModule)
        # compare the regexp from the board yaml file with the model
        return re.match(self.hw_module.id, self.model()) is not None

    # Voltage and Current Interfaces
    def __convert_and_scale(self, attr: str) -> float:
        return self.sysfs.read_float(attr) / 1000.0

    @retry()
    def in1_input(self) -> float:
        """
        Get input voltage of PSU page 1.

        Returns
        -------
            Input voltage in volts
        """
        return self.__convert_and_scale("in1_input")

    @retry()
    def in2_input(self) -> float:
        """
        Get input voltage of PSU page 2.

        Returns
        -------
            Input voltage in volts
        """
        return self.__convert_and_scale("in2_input")

    @retry()
    def curr1_input(self) -> float:
        """
        Get input current of PSU page 1.

        Returns
        -------
            Input current in amperes
        """
        return self.__convert_and_scale("curr1_input")

    @retry()
    def curr2_input(self) -> float:
        """
        Get input current of PSU page 2.

        Returns
        -------
            Input current in amperes
        """
        return self.__convert_and_scale("curr2_input")

    # Status Interface
    @retry()
    def status0_input(self) -> PSUStatus:
        """
        Get the status of PSU page 1.

        Returns
        -------
            PSU status as defined in PSUStatus
        """
        status = self.sysfs.read_hex("status0_input")
        return PSUStatus(status)

    @retry()
    def status1_input(self) -> PSUStatus:
        """
        Get the status of PSU page 2.

        Returns
        -------
            PSU status as defined in PSUStatus
        """
        status = self.sysfs.read_hex("status1_input")
        return PSUStatus(status)

    # Temperature Interface
    @retry()
    def temp1_input(self) -> float:
        """
        Get the PSU temperature.

        Returns
        -------
            PSU temperature in degrees celsius
        """
        return self.__convert_and_scale("temp1_input")

    # Inventory Interface
    def vendor(self) -> str:
        """
        Get the vendor of the PSU.

        Returns
        -------
            PSU vendor
        """
        return self.sysfs.read_utf8("vendor")

    def model(self) -> str:
        """
        Get the model of the PSU.

        Returns
        -------
            PSU model
        """
        return self.sysfs.read_utf8("model")

    def serial(self) -> str:
        """
        Get the serial number of the PSU.

        Returns
        -------
            PSU serial number
        """
        return self.sysfs.read_utf8("serial")

    def revision(self) -> str:
        """
        Get the revision of the PSU.

        Returns
        -------
            PSU revision
        """
        return self.sysfs.read_utf8("revision")
