from ekfsm.core.components import SysTree
from ekfsm.log import ekfsm_logger
from ekfsm.utils import next_or_raise

from ..core.sysfs import list_sysfs_attributes
from .generic import Device
from .iio import iio_get_in_value


class IIOThermalHumidity(Device):
    """
    Device for IIO thermal and/or humidity sensors.

    Parameters
    ----------
    name
        The name of the device.
    parent
        The parent device of the IIOThermalHumidity device. If None, no parent is created.
    children
        The children of the IIOThermalHumidity device. If None, no children are created.
    """

    def __init__(
        self,
        name: str,
        parent: SysTree | None = None,
        children: list[Device] | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        self.logger = ekfsm_logger("IIOThermalHumidity:" + name)
        super().__init__(name, parent, children, abort, *args, **kwargs)
        self.addr = self.get_i2c_chip_addr()
        self.sysfs_device = self.get_i2c_sysfs_device(self.addr, False)

        # TODO: We can just search the attributes directly
        iio_dir = self.sysfs.path.glob("iio:device*")
        attrs = next_or_raise(iio_dir, FileNotFoundError("IIO entry not found"))

        self.sysfs_device.extend_attributes(list_sysfs_attributes(attrs))

    def temperature(self) -> float:
        return iio_get_in_value(self.sysfs, "in_temp") / 1000.0

    def humidity(self) -> float:
        return iio_get_in_value(self.sysfs, "in_humidityrelative") / 1000.0
