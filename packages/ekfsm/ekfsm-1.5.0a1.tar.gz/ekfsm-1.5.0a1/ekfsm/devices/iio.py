from ekfsm.exceptions import ConversionError, SysFSError

from .generic import SysfsDevice


def iio_get_in_value(dev: SysfsDevice, attrset: str) -> float:
    """
    Calculate a value from an IIO in_* attribute set, using the _raw, _scale and _offset attributes (if present).
    Typical name of attrset are "in_temp" or "in_voltage0".

    Formula according to https://wiki.st.com/stm32mpu/wiki/How_to_use_the_IIO_user_space_interface

    Parameters
    ----------
    dev
        sysfs device object pointing to the iio directory
    attrset
        name of the attribute set to read from (e.g. "in_temp")

    Returns
    -------
    float
        calculated value from the attribute set (no unit conversion)

    Raises
    ------
    FileNotFoundError
        if the neiter _input nor _raw attribute is found

    """
    try:
        content = dev.read_float(f"{attrset}_input")
    except (SysFSError, ConversionError):
        try:
            raw = dev.read_float(f"{attrset}_raw")
            offset = dev.read_float(f"{attrset}_offset")
            scale = dev.read_float(f"{attrset}_scale")
            content = (raw + offset) * scale
        except (SysFSError, ConversionError) as e:
            raise FileNotFoundError from e

    return content
