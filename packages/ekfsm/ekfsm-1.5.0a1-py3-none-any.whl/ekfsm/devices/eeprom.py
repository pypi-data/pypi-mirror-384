"""
A module containing classes to represent EEPROM devices.

Routine Listings
----------------
    :py:class:`EEPROM`
    :py:class:`Validatable_EEPROM`
    :py:class:`EKF_EEPROM`
    :py:class:`validated`
"""

from abc import ABC, abstractmethod
from datetime import date
from functools import wraps
from typing import Any, Callable, Literal, Sequence

from hexdump import hexdump

from ekfsm.core.components import SysTree
from ekfsm.core.probe import ProbeableDevice
from ekfsm.exceptions import DataCorruptionError, DriverError, SysFSError
from ekfsm.log import ekfsm_logger

from .generic import Device
from .utils import get_crc16_xmodem

logger = ekfsm_logger(__name__)


def validated(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator to validate the CRC of the EEPROM content before executing a method.

    Parameters
    ----------
    func
        The method to validate.

    Note
    ----
    This decorator should be used on methods that read data from an EEPROM.
    """

    @wraps(func)
    def validate(self, *args, **kwargs):
        logger.debug(f"Validating EEPROM content for {self.name}")
        if not self.valid:
            raise DataCorruptionError("CRC validation failed")
        logger.debug(f"EEPROM content is valid for {self.name}")
        return func(self, *args, **kwargs)

    return validate


class EEPROM(Device):
    """
    A class used to represent a generic EEPROM device.

    Parameters
    ----------
    name
        The name of the EEPROM device.
    parent
        The parent device of the EEPROM in the :py:class:`~.generic.Device` tree.


    Caution
    -------
    The following conditions must be met for this class to work properly:
        - EEPROM must be I2C accessable
        - EEPROM must have a sysfs device


    Note
    ----
    This class should be inherited by classes representing specific EEPROM devices and defining custom storage schemes.
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
        super().__init__(name, parent, None, abort, *args, **kwargs)

        self.addr = self.get_i2c_chip_addr()
        self.sysfs_device = self.get_i2c_sysfs_device(self.addr)

        if not self.sysfs_device.get_driver():
            raise DriverError("No driver attached to device {self.name}")

        self._update_content()

    def _update_content(self) -> None:
        """
        Update the content of the EEPROM device.


        Note
        ----
            - This method should be called whenever the content of the EEPROM is updated (after each write op).
            - Inheriting classes should call this method before updating their own attributes.
        """
        logger.debug("Reading data")
        try:
            data = self.read()
            self._content = data
        except Exception as e:
            logger.error(f"Error reading data, {e}")
            self._content = b""

    def read(self) -> bytes:
        """
        Read the content of the EEPROM.

        Returns
        -------
            The content of the EEPROM.

        Raises
        ------
        SysFSError
            No sysfs device found for EEPROM or `eeprom` attribute does not exist
        """
        return self.read_sysfs_bytes("eeprom")

    def write(self, data: bytes, offset: int = 0) -> None:
        """
        Write data to the EEPROM.

        Parameters
        ----------
        data
            The data to write to the EEPROM.
        offset
            The offset at which to start writing the data.

        Raises
        ------
        RuntimeError
            If the sysfs device is not found.
        FileNotFoundError
            If the EEPROM sysfs file is not found.
        DataCorruptionError
            If an error occurs during the write operation.

        Note
        ----
        Operation is checked for data corruption by reading back the written data.

        Important
        ---------
        The offset parameter is only supported if the EEPROM driver is bin_attribute enabled.

        For almost any other native sysfs attribute, this is NOT the case!
        """

        if self.sysfs_device:
            attr = next(x for x in self.sysfs_device.attributes if x.name == "eeprom")
            logger.info(f"Writing {len(data)} bytes to EEPROM at offset {offset}")
            if attr.is_sysfs_attr() and data is not None:
                mode = "r+" if isinstance(data, str) else "rb+"
            try:
                with open(attr.path, mode) as f:
                    f.seek(offset)
                    f.write(data)
            except OSError as e:
                raise SysFSError("Error accessing SysFS attribute") from e
        else:
            raise RuntimeError("No sysfs device for EEPROM")

        self._update_content()
        written = self._content[offset : offset + len(data)]
        if not written == data:
            raise DataCorruptionError(
                "Error during EEPROM write, data is not the same as read back"
            )

    def print(self):
        hexdump(self._content)


class Validatable_EEPROM(EEPROM, ABC):
    """
    Abstract class used to represent an EEPROM device using CRC to validate its content.

    Parameters
    ----------
    crc_pos
        The position of the CRC value in the EEPROM content (`'start'` or `'end'`).
    crc_length
        The length of the CRC value in number of bytes (defaults to 2).

    Note
    ----
    - Derived classes must implement a method to compute the CRC value of the EEPROM content.
    - If the CRC position differs from the shipped schema `('start' | 'end')`,
      the derived class must override the :meth:`~Validatable_EEPROM._update_content` method.
    - Validity of individual content fields stored/returned by attributes, methods or properties
      can be achieved by using the :py:func:`validated` decorator.

    See Also
    --------
    Validatable_EEPROM._compute_crc : Method to compute the CRC value of the EEPROM content.
    """

    def __init__(
        self,
        name: str,
        parent: SysTree | None = None,
        children: list[Device] | None = None,
        abort: bool = False,
        crc_pos: Literal["start", "end"] = "end",
        crc_length: int = 2,
        *args,
        **kwargs,
    ) -> None:
        self._crc_length: int = crc_length
        self._crc_pos: str = crc_pos

        super().__init__(name, parent, children, abort, *args, **kwargs)

        self._crc_pos_start = len(self._data) if self._crc_pos == "end" else 0
        self._crc_pos_end = self._crc_pos_start + self._crc_length

    def _update_content(self) -> None:
        """
        Update the content of the EEPROM device (checksum excluded).
        """
        super()._update_content()

        # Firmware data without CRC
        self._data: bytes = (
            self._content[self._crc_length :]
            if self._crc_pos == "start"
            else self._content[: -self._crc_length :]
        )

    def _update_crc(self) -> None:
        """
        Update the CRC value of the EEPROM content.
        """
        self.crc = self._compute_crc()

    def _get_crc_value(self) -> int:
        return int.from_bytes(
            self._content[self._crc_pos_start : self._crc_pos_end], byteorder="little"
        )

    @property
    def crc(self) -> int:
        """
        Gets or sets the CRC value of the EEPROM content.

        Parameters
        ----------
        value: optional
            The CRC value to write to the EEPROM.

        Returns
        -------
            int
                The CRC value currently stored in the EEPROM if used as *getter*.
            None
                If used as *setter*.


        Caution
        -------
        The *setter* actually writes the CRC value to the EEPROM.


        Warning
        -------
        The *setter* method should be used with caution as it can lead to data corruption if the CRC value is not correct!


        Note
        ----
        The *setter* is usually triggered automatically after a successful write operation
        and in most cases, there is no need to call it manually.
        """
        return self._get_crc_value()

    @crc.setter
    def crc(self, value: int) -> None:
        crc_bytes = value.to_bytes(self._crc_length, byteorder="little")
        logger.debug(f"Writing CRC value {value} to EEPROM")

        try:
            super().write(crc_bytes, self._crc_pos_start)
        except Exception as e:
            logger.error(f"Error writing CRC value to EEPROM, {e}")

        # self._update_content()

    @property
    def valid(self) -> bool:
        """
        Checks if the EEPROM content is valid by comparing the stored CRC value with the computed CRC value.

        Returns
        -------
        bool
            `True` if the EEPROM content is valid, `False` otherwise.
        """
        return self._compute_crc() == self.crc

    @abstractmethod
    def _compute_crc(self) -> int:
        """
        This method should be implemented by derived classes to compute the CRC value of the EEPROM content.

        Returns
        -------
            The computed CRC value.
        """
        pass

    def write(self, data: bytes, offset: int = 0) -> None:
        try:
            super().write(data, offset)
            self._update_crc()
        except Exception as e:
            logger.error(f"Error writing to EEPROM, {e}")


class EKF_EEPROM(Validatable_EEPROM, ProbeableDevice):
    """
    A class used to represent an EKF EEPROM device.

    Structure
    ---------
    The EKF_EEPROM content is structured as follows:

    - `Serial number` (4 bytes, starts at pos 8):
        The serial number of the device.
    - `Manufactured at` (2 bytes, starts at pos 12):
        The date the device was manufactured.
    - `Repaired at` (2 bytes, starts at pos 14):
        The date the device was repaired.
    - `Customer serial number` (4 bytes, starts at pos 32):
        The customer serial number of the device.
    - `Customer configuration block offset pointer` (4 bytes, starts at pos 36):
        The offset pointer to the customer configuration block.
    - `String array` (78 bytes, starts at pos 48):
        An array of strings containing the model, manufacturer, and custom board data of the device.
    - `CRC` (2 bytes, starts at pos 126):
        The CRC value of the EEPROM content.
    - `Raw content` (80 bytes, starts at pos 128):
        Free customizable content for other purposes.


    Note
    ----
    - As the CRC value is stored at the end of the OEM data space, just before the customer configuration block,
      the CRC position is manually set and the :meth:`~ekfsm.devices.eeprom.Validatable_EEPROM._update_content` method is
      overridden.
    - The CRC value is computed using the `CRC-16/XMODEM <https://en.wikipedia.org/wiki/Cyclic_redundancy_check>`_ algorithm.
    - Dates are stored in a proprietary format (2 bytes) and must be decoded using the :meth:`~EKF_EEPROM._decode_date` method.


    See Also
    --------
    `crcmod <https://crcmod.sourceforge.net/>`_


    Important
    ---------
    All data read from the EEPROM should be validated using the @validated decorator.
    This decorator ensures that the data is not corrupted by checking the CRC value.


    Raises
    ------
    DataCorruptionError
        If the CRC validation fails.
    """

    _sernum_index_start = 8
    _sernum_index_end = 12

    _date_mft_index_start = 12
    _date_mft_index_end = 14

    _date_rep_index_start = 14
    _date_rep_index_end = 16

    _customer_serial_index_start = 32
    _customer_serial_index_end = 36

    _customer_config_block_offset_pointer_index = 36

    _str_array_start_offset = 48
    _str_array_end_offset = 126

    def __init__(
        self,
        name: str,
        parent: SysTree | None = None,
        children: list[Device] | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(name, parent, children, abort, *args, **kwargs)

    def _update_content(self) -> None:
        super()._update_content()

        # EKF EEPROM content is restricted to 128 bytes, so strip the rest!
        self._firmware_content = self._content[:128]

        # The rest is raw content available for other purposes
        self._raw_content: bytes = self._content[128:]

        # Firmware data without CRC needs to be overriden
        self._data: bytes = (
            self._firmware_content[self._crc_length :]
            if self._crc_pos == "start"
            else self._firmware_content[: -self._crc_length :]
        )
        self._str_list = self._get_string_array()

        self._crc_pos_start = len(self._data)
        self._crc_pos_end = self._crc_pos_start + self._crc_length

    @validated
    def serial(self) -> str:
        """
        Get the serial number of the device to which the EEPROM is attached (the root device).

        Returns
        -------
            The serial number of the root device.
        """
        area = self._content[self._sernum_index_start : self._sernum_index_end]
        sernum = int.from_bytes(area, byteorder="little")
        return str(sernum)

    def write_serial(self, serial: int) -> None:
        """
        Write serial number of the root device to EEPROM.

        Parameters
        ----------
        serial
            The serial number to write to the EEPROM.
        """
        # Check serial number is within bounds
        unsigned_upper_bound = (2**32) - 1
        if serial < 0 or serial > unsigned_upper_bound:
            raise ValueError(
                f"Serial number must be between 0 and {unsigned_upper_bound}"
            )
        serial_bytes = serial.to_bytes(4, byteorder="little")
        self.write(serial_bytes, self._sernum_index_start)

    @validated
    def custom_serial(self) -> str:
        """
        Get the customer serial number of the device to which the EEPROM is attached (the root device).

        Attention
        ---------
        This is a custom - non-OEM - serial number that can be set by the user.

        Returns
        -------
            The customer serial number of the root device.
        """
        area = self._content[
            self._customer_serial_index_start : self._customer_serial_index_end
        ]
        sernum = int.from_bytes(area, byteorder="little")
        return str(sernum)

    def write_custom_serial(self, serial: int) -> None:
        """
        Write customer serial number of the root device to EEPROM.

        Parameters
        ----------
        serial
            The customer serial number to write to the EEPROM.


        Raises
        ------
        ValueError
            If the serial number is not within the bounds of a 32-bit unsigned integer.


        Note
        ----
        Due to space restrictions on storage, the serial number must be a 32-bit unsigned integer.
        """
        # Check serial number is within bounds
        unsigned_upper_bound = (2**32) - 1
        if serial < 0 or serial > unsigned_upper_bound:
            raise ValueError(
                f"Serial number must be between 0 and {unsigned_upper_bound}"
            )

        serial_bytes = serial.to_bytes(4, byteorder="little")
        logger.debug(f"Writing customer serial {serial}")
        self.write(serial_bytes, self._customer_serial_index_start)

    @validated
    def manufactured_at(self) -> date:
        """
        Get the date the device was manufactured.

        Returns
        -------
            The date the device was manufactured.
        """
        area = self._content[self._date_mft_index_start : self._date_mft_index_end]
        # encoded_mft_date = area[::-1]
        return self._decode_date(area)

    @validated
    def repaired_at(self) -> date:
        """
        Get the date the device was repaired.

        Returns
        -------
            The most recent date the device was repaired.
        """
        area = self._content[self._date_rep_index_start : self._date_rep_index_end]
        # encoded_rep_date = area[::-1]
        return self._decode_date(area)

    @validated
    def write_repaired_at(self, date: date) -> None:
        """
        Write the date the device was repaired to EEPROM.

        Parameters
        ----------
        date
            The date the device was repaired.

        Note
        ----
        The date year must be within the range of 1980-2079.

        Attention
        ---------
        The date is stored in a proprietary 2-byte format.

        Raises
        ------
        ValueError
            If the year is not within the range of 1980-2079.
        """
        if date.year < 1980 or date.year > 2079:
            raise ValueError("Year must be within the range of 1980-2079")
        rep_date_bytes = self._encode_date(date)
        logger.debug(f"Writing repair date {date} to EEPROM")
        self.write(rep_date_bytes, self._date_rep_index_start)

    @validated
    def model(self) -> str | None:
        """
        Get the model name of the device to which the EEPROM is attached to (the root device).

        Returns
        -------
            The model name of the device.
        """
        return self._str_list[0] if len(self._str_list) > 0 else None

    @validated
    def vendor(self) -> str | None:
        """
        Get the vendor/manufacturer of the device to which the EEPROM is attached to (the root device).

        Returns
        -------
            The name of the vendor/manufacturer of the device.
        """
        return self._str_list[1] if len(self._str_list) > 1 else None

    @validated
    def custom_board_data(self) -> str | None:
        """
        Get the custom board data of the device.

        Note
        ----
        This is a custom field that can be set by the user.


        Attention
        ---------
        This field is optional and may not be present in the EEPROM content.


        Returns
        -------
            The custom board data of the device as a string, or `None` if the field is not present.
        """
        return None if len(self._str_list) < 3 else self._str_list[2]

    def write_custom_board_data(self, data: str) -> None:
        """
        Write custom board data to EEPROM.

        Important
        ---------
        Due to size limitations, the custom board data should only contain expressive,
        short content like serials, variants or specific codes.

        Parameters
        ----------
        data
            The custom board data to write to the EEPROM.

        Attention
        ---------
        The model and vendor fields are mandatory and must be set before writing custom board data.

        Raises
        ------
        ValueError
            If the model and vendor fields are not set before writing custom board data.
        """
        data_bytes = data.encode("utf-8")
        data_offset = 0
        for s in self._str_list[:2]:
            if s is None:
                raise ValueError(
                    "Model and vendor fields must be set before writing custom board data"
                )
            if isinstance(s, str):
                data_offset += len(s) + 1
        logger.info(f"Writing custom board data {data} to EEPROM")
        self.write(data_bytes, self._str_array_start_offset + data_offset)

    def custom_raw_data(self) -> bytes:
        """
        Get the raw content area data stored in the EEPROM.

        Returns
        -------
            The data contained in the raw content block of the EEPROM.


        Note
        ----
        This area is free for custom data storage and is not included during crc calculations and validations.


        Important
        ---------
        If custom raw data should be stored on EEPROM and
        if it should be protected against corruption, it has to be validated manually.
        """
        return self._raw_content

    def write_custom_raw_data(self, data: bytes) -> None:
        """
        Write custom data to the raw content area of the EEPROM.

        Parameters
        ----------
        data
            The data to write to the raw content area of the EEPROM.
        """
        logger.info(f"Writing {len(data)} bytes to raw content area of EEPROM")
        self.write(data, 128)

    def _get_string_array(self) -> list[str | None]:
        str_array = self._content[
            self._str_array_start_offset : self._str_array_end_offset
        ].split(b"\x00")
        try:
            return [s.decode("utf-8") for s in str_array if s]
        except UnicodeDecodeError:
            return [None, None, None]

    @classmethod
    def _decode_date(cls, encoded_date: Sequence[int]) -> date:
        """
        Decode a date from a proprietary 2-byte format.

        Parameters
        ----------
        encoded_date
            The date to decode.

        Raises
        ------
        ValueError
            If the date is invalid (e.g., 30th Feb).

        Returns
        -------
        date
            The decoded date.
        """
        bdate = int.from_bytes(encoded_date, byteorder="little")

        # Extract the day (bit 0-4)
        day = bdate & 0x1F  # 0x1F is 00011111 in binary (5 bits)

        # Extract the month (bit 5-8)
        month = (bdate >> 5) & 0x0F  # Shift right by 5 and mask with 0x0F (4 bits)

        # Extract the year since 1980 (bit 9-15)
        year = (bdate >> 9) & 0x7F  # Shift right by 9 and mask with 0x7F (7 bits)
        year += 1980  # Add base year (1980)

        # Return a datetime object with the extracted year, month, and day
        try:
            decoded_date = date(year, month, day)
            return decoded_date
        except ValueError:
            raise ValueError(
                f"Invalid date: {day}/{month}/{year}"
            )  # Handle invalid dates, e.g., 30th Feb

    @classmethod
    def _encode_date(cls, date: date) -> bytes:
        """
        Encode a date into a proprietary 2-byte format.

        Parameters
        ----------
        date
            The date to encode.

        Returns
        -------
        bytes
            The encoded date.
        """
        year = date.year - 1980
        month = date.month
        day = date.day

        encoded_date = year << 9 | month << 5 | day
        return encoded_date.to_bytes(2, byteorder="little")

    def _compute_crc(self) -> int:
        return get_crc16_xmodem(self._data)

    def probe(self, *args, **kwargs):
        return self.hw_module.id == self.model()


class EKF_CCU_EEPROM(EKF_EEPROM):
    """
    EKF CCU EEPROM - uses the second part of the EEPROM for chassis inventory and customer area
    """

    _cvendor_index_start = 128
    _cvendor_length = 24

    _cmodel_index_start = 152
    _cmodel_length = 24

    _crevision_index_start = 176
    _crevision_length = 9

    _cserial_index_start = 185
    _cserial_length = 4

    _unit_index_start = 189
    _unit_length = 1

    _customer_area_start = 190
    _customer_area_length = 63

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def _update_content(self) -> None:
        super()._update_content()

        # CCU content is the raw content area of the EEPROM
        self._ccu_content: bytes = self._raw_content

        # CCU Firmware data without CRC needs to be overriden
        self._cdata: bytes = (
            self._ccu_content[self._crc_length :]
            if self._crc_pos == "start"
            else self._ccu_content[: -self._crc_length :]
        )
        self._ccrc_pos_start = len(self._cdata) + 128
        self._ccrc_pos_end = self._ccrc_pos_start + self._crc_length

    def _update_ccrc(self) -> None:
        """
        Update the CRC value of the EEPROM content.
        """
        self.ccrc = self._compute_ccrc()

    def _get_ccrc_value(self) -> int:
        return int.from_bytes(
            self._content[self._ccrc_pos_start : self._ccrc_pos_end], byteorder="little"
        )

    @property
    def ccrc(self) -> int:
        """
        Gets or sets the CRC value of the EEPROM content.

        Parameters
        ----------
        value: optional
            The CRC value to write to the EEPROM.

        Returns
        -------
            int
                The CRC value currently stored in the EEPROM if used as *getter*.
            None
                If used as *setter*.


        Caution
        -------
        The *setter* actually writes the CRC value to the EEPROM.


        Warning
        -------
        The *setter* method should be used with caution as it can lead to data corruption if the CRC value is not correct!


        Note
        ----
        The *setter* is usually triggered automatically after a successful write operation
        and in most cases, there is no need to call it manually.
        """
        return self._get_ccrc_value()

    @ccrc.setter
    def ccrc(self, value: int) -> None:
        ccrc_bytes = value.to_bytes(self._crc_length, byteorder="little")
        logger.debug(f"Writing chassis CRC value {value}")
        try:
            super(Validatable_EEPROM, self).write(ccrc_bytes, self._ccrc_pos_start)
        except Exception as e:
            logger.error(f"Error writing CRC value, error: {e}")

    @property
    def valid(self) -> bool:
        """
        Checks if the EEPROM content is valid by comparing the stored CRC value with the computed CRC value.

        Returns
        -------
        bool
            `True` if the EEPROM content is valid, `False` otherwise.
        """
        return self._compute_ccrc() == self.ccrc and super().valid

    @validated
    def cvendor(self) -> str:
        """
        Get the chassis vendor.

        Returns
        -------
            The vendor of the chassis.
        """

        return (
            self._content[
                self._cvendor_index_start : self._cvendor_index_start
                + self._cvendor_length
            ]
            .strip(b"\x00")
            .decode("utf-8")
        )

    def write_cvendor(self, vendor: str) -> None:
        """
        Write the vendor of the chassis to EEPROM.

        Parameters
        ----------
        vendor
            The vendor of the chassis.
        """
        vendor_bytes = vendor.encode("utf-8")
        vendor_fill = b"\x00" * (self._cvendor_length - len(vendor_bytes))
        vendor_bytes += vendor_fill
        logger.info(f"Writing vendor {vendor}")
        self.write(vendor_bytes, self._cvendor_index_start)

    @validated
    def cmodel(self) -> str:
        """
        Get the chassis model.

        Returns
        -------
            The model of the chassis.
        """
        return (
            self._content[
                self._cmodel_index_start : self._cmodel_index_start
                + self._cmodel_length
            ]
            .strip(b"\x00")
            .decode("utf-8")
        )

    def write_cmodel(self, model: str) -> None:
        """
        Write the model of the chassis to EEPROM.

        Parameters
        ----------
        model
            The model of the chassis.
        """
        model_bytes = model.encode("utf-8")
        model_fill = b"\x00" * (self._cmodel_length - len(model_bytes))
        model_bytes += model_fill
        logger.info(f"Writing model {model}")
        self.write(model_bytes, self._cmodel_index_start)

    @validated
    def cserial(self) -> int:
        """
        Get the chassis serial number.

        Returns
        -------
            The serial number of the chassis.
        """
        area = self._content[
            self._cserial_index_start : self._cserial_index_start + self._cserial_length
        ]
        cserial = int.from_bytes(area, byteorder="little")
        return cserial

    def write_cserial(self, serial: int) -> None:
        """
        Write the serial number of the chassis to EEPROM.

        Parameters
        ----------
        serial
            The serial number of the chassis.
        """
        # Check serial number is within bounds
        unsigned_upper_bound = (2**32) - 1
        if serial < 0 or serial > unsigned_upper_bound:
            raise ValueError(
                f"Serial number must be between 0 and {unsigned_upper_bound}"
            )
        serial_bytes = serial.to_bytes(4, byteorder="little")
        logger.info(f"Writing chassis serial {serial}")
        self.write(serial_bytes, self._cserial_index_start)

    @validated
    def crevision(self) -> str:
        """
        Get the revision of the chassis.

        Returns
        -------
            The revision of the chassis.
        """
        return (
            self._content[
                self._crevision_index_start : self._crevision_index_start
                + self._crevision_length
            ]
            .strip(b"\x00")
            .decode("utf-8")
        )

    def write_crevision(self, revision: str) -> None:
        """
        Write the chassis revision.

        Parameters
        ----------
        revision
            The revision of the chassis.
        """
        revision_bytes = revision.encode("utf-8")
        revision_fill = b"\x00" * (self._crevision_length - len(revision_bytes))
        revision_bytes += revision_fill
        logger.info(f"Writing chassis revision {revision}")
        self.write(revision_bytes, self._crevision_index_start)

    @validated
    def unit(self) -> int:
        """
        Get the subsystem unit number.

        Returns
        -------
            The unit number of the subsystem.
        """
        area = self._content[self._unit_index_start]
        unit = int.from_bytes([area], byteorder="little")
        return unit

    @validated
    def version(self) -> int:
        """
        Get the version of the EEPROM data scheme.

        Note
        ----
        If undefined, the version is set to 255 and then defaults to 0.

        Returns
        -------
            The version of the EEPROM data scheme.
        """
        version = self._content[self._ccrc_pos_start - 1]
        return version

    def write_version(self, version: int) -> None:
        """
        Write the version of the EEPROM data scheme.

        Parameters
        ----------
        version
            The version of the EEPROM data scheme.
        """
        if version < 0 or version > 255:
            raise ValueError("Version must be between 0 and 255")

        if version == 255:
            logger.warning("Version 255 is undefined, setting to 0")
            version = 0

        version_bytes = version.to_bytes(1, byteorder="little")
        logger.info(f"Writing version {version}")
        self.write(version_bytes, self._ccrc_pos_start - 1)

    def write_unit(self, unit: int) -> None:
        """
        Write the subsystem unit number.

        Parameters
        ----------
        unit
            The unit number of the subsystem.
        """
        unit_bytes = unit.to_bytes(1, byteorder="little")
        logger.info(f"Writing unit {unit}")
        self.write(unit_bytes, self._unit_index_start)

    @validated
    def customer_area(self) -> bytes:
        """
        Get the customer area of the CCU EEPROM.

        Returns
        -------
            The customer area of the CCU EEPROM.
        """
        return self._content[
            self._customer_area_start : self._customer_area_start
            + self._customer_area_length
        ]

    def write_customer_area(self, data: bytes) -> None:
        """
        Write data to CCU EEPROM customer area.

        Parameters
        ----------
        data
            The data to write to the customer area of the CCU EEPROM.

        Raises
        ------
        ValueError
            If the data exceeds the customer area length.

        Example
        -------
        >>> eeprom = EKF_CCU_EEPROM()
        >>> eeprom.write_customer_area(b"Hello, World!")
        >>> eeprom.customer_area()
        b'Hello, World!'
        """
        if len(data) > self._customer_area_length:
            raise ValueError("Data exceeds customer area length")
        self.write(data, self._customer_area_start)

    def _compute_ccrc(self) -> int:
        return get_crc16_xmodem(self._cdata)

    def write(self, data: bytes, offset: int = 0) -> None:
        try:
            super(Validatable_EEPROM, self).write(data, offset)
        except Exception as e:
            logger.error(f"Error writing to EEPROM, {e}")
        self._update_ccrc()

    def custom_raw_data(self) -> bytes:
        raise NotImplementedError("CCU EEPROM does not have a raw content area")

    def write_custom_raw_data(self, data: bytes) -> None:
        raise NotImplementedError("CCU EEPROM does not have a raw content area")
