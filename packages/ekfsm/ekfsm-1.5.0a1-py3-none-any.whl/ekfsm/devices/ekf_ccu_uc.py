import struct
from enum import Enum
from typing import Any, Tuple

from smbus2 import SMBus

from ekfsm.core.components import SysTree

from ..exceptions import AcquisitionError
from ..lock import Locker
from .generic import Device
from .imu import ImuSample


class CcuCommands(Enum):
    NOP = 0x01
    IMU_SAMPLES = 0x10
    FAN_STATUS = 0x11
    VIN_VOLTAGE = 0x12
    CCU_TEMPERATURE = 0x13
    CCU_HUMIDITY = 0x14
    PUSH_TEMPERATURE = 0x15
    SW_SHUTDOWN = 0x16
    WD_TRIGGER = 0x17
    IDENTIFY_FIRMWARE_TITLE = 0x80
    IDENTIFY_FIRMWARE_VERSION = 0x81
    LOAD_FIRMWARE_CHUNK = 0x82
    LOAD_PARAMETERSET = 0x83
    GET_PARAMETERSET_BEGIN = 0x84
    GET_PARAMETERSET_FOLLOW = 0x85
    RESTART = 0x8F


class EKFCcuUc(Device):
    """
    A class to communicate with I2C microcontroller on the EKF CCU.
    """

    def __init__(
        self,
        name: str,
        parent: SysTree | None,
        children: list["Device"] | None = None,
        abort: bool = False,
        debug: Any = None,  # XXX: What is this?
        *args,
        **kwargs,
    ):
        super().__init__(name, parent, None, abort, *args, **kwargs)
        self._i2c_addr = self.get_i2c_chip_addr()
        self._i2c_bus = self.get_i2c_bus_number()
        self._smbus = SMBus(self._i2c_bus)

    def __str__(self) -> str:
        return (
            f"EKFCCU - I2C Bus/Address: {self._i2c_bus}/{hex(self._i2c_addr)}; "
            f"sysfs_path: {self.sysfs_device.path if self.sysfs_device else ''}"
        )

    def temperature(self) -> float:
        """
        Get the temperature from the CCU thermal/humidity sensor.

        Note
        ----
        The CCU reads the temperature once per second.

        Returns
        -------
        float
            The temperature in degrees Celsius.

        Raises
        ------
        AcquisitionError
            If the temperature cannot be read, for example, because the sensor is not working.
        """
        return self._get_signed_word_data(CcuCommands.CCU_TEMPERATURE.value, "temperature") / 10.0

    def humidity(self) -> float:
        """
        Get the relative humidity from the CCU thermal/humidity sensor.
        The humidity is read once per second.

        Returns
        -------
        float
            The relative humidity in percent.

        Raises
        ------
        AcquisitionError
            If the humidity cannot be read, for example, because the sensor is not working.
        """
        return self._get_signed_word_data(CcuCommands.CCU_HUMIDITY.value, "humidity") / 10.0

    def vin_voltage(self) -> float:
        """
        Get the system input voltage from the CCU (the pimary voltage of the PSU).
        The voltage is read every 100ms.

        Returns
        -------
        float
            The system input voltage in volts.

        Raises
        ------
        AcquisitionError
            If the voltage cannot be read, for example, because the ADC is not working.
        """
        return self._get_signed_word_data(CcuCommands.VIN_VOLTAGE.value, "VIN voltage") / 10.0

    def _get_signed_word_data(self, cmd: int, what: str) -> int:
        v = self._smbus.read_word_data(self._i2c_addr, cmd)

        if v == 0x8000:
            raise AcquisitionError(f"Cannot read {what}")

        return struct.unpack("<h", struct.pack("<H", v))[0]

    def fan_status(self, fan: int) -> Tuple[float, float, int]:
        """
        Get the status of a fan.

        Parameters
        ----------
        fan
            The fan number (0-2).

        Returns
        -------
        desired: float
            The desired speed.
        actual: float
            The actual speed.
        diag: int
            The diagnostic value.

        Note
        ----
        The diagnostic value is a bitfield with the following meaning:

            - bit 0: 0 = fan status is invalid, 1 = fan status is valid
            - bit 1: 0 = no error detected, 1 = fan is stuck
        """
        data = self._smbus.read_block_data(self._i2c_addr, CcuCommands.FAN_STATUS.value)
        _data = bytes(data)
        desired, actual, diag = struct.unpack("<HHB", _data[fan * 5 : fan * 5 + 5])
        return desired, actual, diag

    def push_temperature(self, fan: int, temp: float) -> None:
        """
        Tell FAN controller the external temperature, usually the CPU temperature.

        Parameters
        ----------
        fan
            The fan number (0-2), or -1 to set the external temperature of all fans.

        temp
            The external temperature in degrees Celsius.

        Important
        ---------
        If push_temperature is no more called for a certain time (configurable with `fan-push-tout` parameter),
        the fan controller will fallback to it's default fan speed (configurable with the `fan-defrpm` parameter).

        """
        if fan == -1:
            fan = 0xFF
        data = struct.pack("<Bh", fan, int(temp * 10))
        self._smbus.write_block_data(self._i2c_addr, CcuCommands.PUSH_TEMPERATURE.value, list(data))

    def imu_sample(self) -> Tuple[ImuSample | None, bool]:
        """
        Read the next IMU sample from the CCU's IMU sample FIFO.

        If no sample is available, this method returns None.
        The second return value indicates if more samples are available in the FIFO.

        The CCU periodically samples the accelerometer and gyroscope data from the IMU and
        places it into a FIFO of 256 entries.
        Application must periodically read the samples from the FIFO to avoid overflow.

        FIFO overflow is indicated in the sample by the `lost` attribute.

        Note that the x, y, and z axes of the accelerometer and gyroscope
        are aligned to the mounting of the IMU on the CCU board. Please correct the axes if necessary
        to match the orientation of the IMU in your application.

        Returns
        -------
        imu_data: ImuSample | None
            The IMU sample, or None if no sample is available.
        more_samples: bool
            True if more samples are available in the FIFO, False otherwise.
        """
        more_samples = False
        _data = self._smbus.read_block_data(self._i2c_addr, CcuCommands.IMU_SAMPLES.value)
        data = bytes(_data)
        if len(data) < 14:
            return None, False  # No data available
        diag, fsr, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z = struct.unpack("<BBhhhhhh", data)
        imu_data = ImuSample(
            [
                self._scale_imu_accel(acc_x, fsr),
                self._scale_imu_accel(acc_y, fsr),
                self._scale_imu_accel(acc_z, fsr),
            ],
            [
                self._scale_imu_gyro(gyro_x, fsr),
                self._scale_imu_gyro(gyro_y, fsr),
                self._scale_imu_gyro(gyro_z, fsr),
            ],
            True if diag & 1 else False,
        )

        more_samples = True if (diag & 2 != 0) else False

        return imu_data, more_samples

    @staticmethod
    def _scale_imu_accel(val: int, fsr: int) -> float:
        fsr = fsr & 0xF
        scale = 16 / (1 << fsr)
        return val * (scale / 32768) * 9.80665  # convert to m/s^2

    @staticmethod
    def _scale_imu_gyro(val: int, fsr: int) -> float:
        fsr = fsr >> 4 & 0xF
        scale = 2000 / (1 << fsr)
        return val * (scale / 32768)

    def sw_shutdown(self) -> None:
        """
        Tell CCU that the system is going to shutdown.
        This cause the CCU's system state controller to enter shutdown state and power off the system after a certain time
        (parameter `shutdn-delay`).

        """
        self._smbus.write_byte(self._i2c_addr, CcuCommands.SW_SHUTDOWN.value)

    def wd_trigger(self) -> None:
        """
        Trigger the CCU's application watchdog.
        This will reset the watchdog timer.

        The CCU watchdog is only enabled when the parameter `wd-tout` is set to a value greater than 0. Triggering
        the watchdog when the timeout is 0 will have no effect.

        If the watchdog is not reset within the timeout, the CCU will power cycle the system.
        """
        self._smbus.write_byte(self._i2c_addr, CcuCommands.WD_TRIGGER.value)

    #
    # Management commands
    #
    def identify_firmware(self) -> Tuple[str, str]:
        """
        Get the firmware title and version of the CCU.

        Returns
        -------
        title: str
            The firmware title.
        version: str
            The firmware version.
        """
        title = bytes(self._smbus.read_block_data(self._i2c_addr, CcuCommands.IDENTIFY_FIRMWARE_TITLE.value)).decode(
            "utf-8"
        )
        version = bytes(
            self._smbus.read_block_data(self._i2c_addr, CcuCommands.IDENTIFY_FIRMWARE_VERSION.value)
        ).decode("utf-8")
        return title, version

    def load_firmware(self, firmware: bytes, progress_callback=None) -> None:
        """
        Load firmware into the CCU.

        The firmware must be the binary firmware file containing the application partition,
        typically named `fw-ccu-mm-default.bin`,
        where `mm` is the major version of the CCU hardware.

        The download can take several minutes, that is why a progress callback can be provided.

        When the download is complete and successful, the CCU will restart. To check if the firmware was loaded successfully,
        call :meth:`identify_firmware()` after the restart.

        Parameters
        ----------
        firmware
            The firmware binary data.

        progress_callback
            A callback function that is called with the current progress in bytes.

        Example
        -------
        >>> from ekfsm.devices import EkfCcuUc
        >>> ccu = EkfCcuUc("ccu")
        >>> firmware = open("fw-ccu-1.0.0.bin", "rb").read()
        >>> # Load firmware with progress callback
        >>> ccu.load_firmware(firmware, progress_callback=lambda x: print(f"Progress: {x} bytes"))
        """
        with Locker(self.name + "-load_firmware").lock():
            offset = 0
            max_chunk_len = 28

            while len(firmware) > 0:
                chunk, firmware = firmware[:max_chunk_len], firmware[max_chunk_len:]
                self._load_firmware_chunk(offset, len(firmware) == 0, chunk)
                offset += len(chunk)

                if len(firmware) != 0:
                    self._nop()

                if progress_callback is not None:
                    progress_callback(offset)

    def _load_firmware_chunk(self, offset: int, is_last: bool, data: bytes) -> None:
        if is_last:
            offset |= 0x80000000

        hdr = struct.pack("<I", offset)
        data = hdr + data

        self._smbus.write_block_data(self._i2c_addr, CcuCommands.LOAD_FIRMWARE_CHUNK.value, list(data))

    def get_parameterset(self) -> str:
        """
        Get the CCU parameterset in JSON format.

        A typical parameterset looks like this:

        .. code-block:: json

            {
                "version":      "factory",
                "parameters":   {
                        "num-fans":     "2",
                        "fan-temp2rpm": "25:2800;50:5000;100:6700",
                        "fan-rpm2duty": "2800:55;5000:88;6700:100",
                        "fan-defrpm":   "5500",
                        "fan-ppr":      "2",
                        "fan-push-tout":        "4000",
                        "pon-min-temp": "-25",
                        "pon-max-temp": "70",
                        "shutdn-delay": "120",
                        "wd-tout":      "0",
                        "pwrcycle-time":        "10"
                },
                "unsupported_parameters":       [],
                "missing_parameters":   ["num-fans", "fan-temp2rpm", "fan-rpm2duty", "fan-defrpm", "fan-ppr", \
                    "fan-push-tout", "pon-min-temp", "pon-max-temp", "shutdn-delay", "wd-tout", "pwrcycle-time"],
                "invalid_parameters":   [],
                "reboot_required":      false
            }

        `version` is the version of the parameterset. If no parameterset has been loaded by the user, the version is `factory`,
        otherwise it is the version of the loaded parameterset.

        `parameters` contains the current values of all parameters of the parameterset.

        `unsupported_parameters` contains the names of parameters that might have been downloaded, but
        are not supported by the CCU firmware.

        `missing_parameters` contains the names of parameters that have not been downloaded yet. Those parameters will
        have their default values.

        `invalid_parameters` contains the names of parameters that have been downloaded, but have invalid values.
        Those parameters will have their default values.

        `reboot_required` is a flag that indicates if a reboot is required to apply the parameterset.


        Returns
        -------
        str
            The parameterset in JSON format.

        """
        with Locker(self.name + "-parameterset").lock():
            json = b""
            begin = True

            while True:
                chunk = self._get_parameterset_chunk(begin)
                if len(chunk) < 32:
                    break
                # if chunk ends with zero byte, remove it (workaround for I2C slave bug)
                if chunk[-1] == 0:
                    chunk = chunk[:-1]
                json += chunk
                begin = False

            return json.decode("utf-8")

    def _get_parameterset_chunk(self, begin: bool) -> bytes:
        data = self._smbus.read_block_data(
            self._i2c_addr,
            (CcuCommands.GET_PARAMETERSET_BEGIN.value if begin else CcuCommands.GET_PARAMETERSET_FOLLOW.value),
        )
        return bytes(data)

    def load_parameterset(self, _cfg: str) -> None:
        """
        Load a parameterset into the CCU.

        The parameterset must be a JSON string containing the parameterset, for example:

        .. code-block:: json

            {
                "version": "1.0.0",
                "parameters":   {
                    "fan-defrpm": "6000"
                }
            }


        This would load a parameterset with just one parameter, the default fan speed. All other parameters will
        be set to their default values.

        Important
        ---------
        In order to apply the parameterset, the CCU must be restarted.

        Parameters
        ----------
        _cfg
            The parameterset in JSON format.

        Example
        -------
        >>> from ekfsm.devices import EkfCcuUc
        >>> ccu = EkfCcuUc("ccu")
        >>> # Load parameterset
        >>> ccu.load_parameterset('{"version": "1.0.0", "parameters": {"fan-defrpm": "6000"}}')
        >>> # Restart CCU to apply parameterset
        >>> ccu.restart()
        """
        with Locker(self.name + "-parameterset").lock():
            cfg = _cfg.encode("utf-8")
            offset = 0
            max_chunk_len = 28

            while len(cfg) > 0:
                chunk, cfg = cfg[:max_chunk_len], cfg[max_chunk_len:]
                self._load_parameterset_chunk(offset, len(cfg) == 0, chunk)
                offset += len(chunk)
                self._nop()

    def _load_parameterset_chunk(self, offset: int, is_last: bool, data: bytes) -> None:
        if is_last:
            offset |= 0x80000000

        hdr = struct.pack("<I", offset)
        data = hdr + data

        self._smbus.write_block_data(self._i2c_addr, CcuCommands.LOAD_PARAMETERSET.value, list(data))

    def restart(self) -> None:
        """
        Restart the CCU.
        """
        self._smbus.write_byte(self._i2c_addr, CcuCommands.RESTART.value)

    def _nop(self) -> None:
        self._smbus.read_word_data(self._i2c_addr, CcuCommands.NOP.value)
