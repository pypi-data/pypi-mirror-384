from ekfsm.devices.coretemp import CoreTemp
from ekfsm.devices.generic import Device
from ekfsm.devices.smbios import SMBIOS
from ekfsm.devices.thermal_humidity import ThermalHumidity

from .eeprom import EEPROM, EKF_CCU_EEPROM, EKF_EEPROM
from .ekf_ccu_uc import EKFCcuUc
from .ekf_sur_led import EKFSurLed
from .gpio import GPIO, EKFIdentificationIOExpander, GPIOExpander
from .iio_thermal_humidity import IIOThermalHumidity
from .mux import I2CMux, MuxChannel
from .pmbus import PMBus, PSUStatus
from .io4edge import IO4Edge
from .pixelDisplay import PixelDisplay
from .buttonArray import ButtonArray
from .button import Button
from .colorLed import ColorLED
from .ledArray import LEDArray
from .watchdog import Watchdog

CLASS_MAP = {
    "GenericDevice": Device,
    "I2CMux": I2CMux,
    "MuxChannel": MuxChannel,
    "GPIO": GPIO,
    "GPIOExpander": GPIOExpander,
    "EKFIdentificationIOExpander": EKFIdentificationIOExpander,
    "EEPROM": EEPROM,
    "EKF_EEPROM": EKF_EEPROM,
    "EKF_CCU_EEPROM": EKF_CCU_EEPROM,
    "EKFCcuUc": EKFCcuUc,
    "PMBus": PMBus,
    "PSUStatus": PSUStatus,
    "SMBIOS": SMBIOS,
    "HWMON": CoreTemp,
    "EKFSurLed": EKFSurLed,
    "IIOThermalHumidity": IIOThermalHumidity,
    "ThermalHumidity": ThermalHumidity,
    "IO4Edge": IO4Edge,
    "PixelDisplay": PixelDisplay,
    "ButtonArray": ButtonArray,
    "Button": Button,
    "ColorLED": ColorLED,
    "LEDArray": LEDArray,
    "Watchdog": Watchdog,
}
