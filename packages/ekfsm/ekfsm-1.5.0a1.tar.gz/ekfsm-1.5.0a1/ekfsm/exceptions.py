from enum import Enum


class EkfSmException(Exception):
    """Base class for all exceptions in the EKFSM Library"""

    pass


class ConfigError(EkfSmException):
    """Error in configuration"""

    pass


class SysFSError(EkfSmException):
    """Error while handling sysfs pseudo file system"""

    pass


class GPIOError(EkfSmException):
    """Error while handling GPIO"""

    class ErrorType(Enum):
        INVALID_PIN = "Pin not found"
        NO_MATCHING_DEVICE = "No matching device found"
        NO_MAJOR_MINOR = "No major/minor number found"

    pass

    def __init__(self, error_type: ErrorType, details: str | None = None):
        self.error_type = error_type
        self.details = details
        super().__init__(f"{error_type.value}: {details}" if details else error_type.value)


class DriverError(EkfSmException):
    """No driver found for device"""

    pass


class HWMonError(EkfSmException):
    """No HwMon entry found for device"""

    pass


class ConversionError(EkfSmException):
    """Failed to convert"""

    pass


class UnsupportedModeError(EkfSmException):
    """Format not supported"""

    pass


class FirmwareNodeError(EkfSmException):
    """Error while handlig firmware node"""

    pass


class DataCorruptionError(EkfSmException):
    """Error while handling data corruption"""

    def __init__(self, details: str | None = None):
        self.details = details
        super().__init__(f"Data corruption: {details}" if details else "Data corruption")


class AcquisitionError(EkfSmException):
    """Error while handling data acquisition"""

    pass
