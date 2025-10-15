from collections.abc import MutableMapping
from pathlib import Path
from typing import Callable

from more_itertools import first_true

from ekfsm.exceptions import ConversionError, DriverError, SysFSError

SYSFS_ROOT = Path("/sys")


def sysfs_root() -> Path:
    return SYSFS_ROOT


def set_sysfs_root(path: Path) -> None:
    global SYSFS_ROOT
    SYSFS_ROOT = path


def file_is_sysfs_attr(path: Path) -> bool:
    return path.is_file() and not path.stat().st_mode & 0o111


class SysFSAttribute:
    """
    A SysFSAttribute is a singular sysfs attribute located somewhere in */sys*.

    Parameters
    ----------
    path: Path
        Path to the underlying file for the SysFSAttribute instance.
    """

    def __init__(self, path: Path):
        if not path.exists() or not path.is_file():
            raise FileNotFoundError("Invalid sysfs attribute path")

        self.path = path
        self.name: str = path.name

    def read_utf8(self) -> str:
        try:
            return self.path.read_text()
        except OSError as e:
            raise SysFSError("Error accessing SysFS attribute") from e

    def read_bytes(self) -> bytes:
        try:
            return self.path.read_bytes()
        except OSError as e:
            raise SysFSError("Error accessing SysFS attribute") from e

    # FIXME: This cannot work due to sysfs attributes not supporting seek().
    def write(self, data: str | bytes | None, offset: int = 0) -> None:
        if self.is_sysfs_attr() and data is not None:
            mode = "r+" if isinstance(data, str) else "rb+"
            try:
                with open(self.path, mode) as f:
                    f.seek(offset)
                    f.write(data)
            except OSError as e:
                raise SysFSError("Error accessing SysFS attribute") from e

    def is_sysfs_attr(self) -> bool:
        return file_is_sysfs_attr(self.path)

    def __repr__(self):
        return f"SysFSAttribute: {self.name}"


def list_sysfs_attributes(path: Path) -> list[SysFSAttribute]:
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Invalid sysfs directory: {path}")

    return [SysFSAttribute(item) for item in path.iterdir() if file_is_sysfs_attr(item)]


class SysfsDevice(MutableMapping):
    def __init__(
        self, base_dir: Path, driver_required=True, find_driver: Callable | None = None
    ):
        self.path: Path = base_dir
        self.driver_required = driver_required

        try:
            self.driver = self.get_driver()
        except Exception:
            self.driver = None

            if driver_required:
                raise DriverError(f"No driver found for device at {base_dir}")

        try:
            self.attributes: list[SysFSAttribute] = list_sysfs_attributes(self.path)
        except FileNotFoundError as e:
            raise SysFSError(f"SysFS entry for {base_dir} does not exist") from e

    def __getitem__(self, key):
        if (
            attr := first_true(self.attributes, pred=lambda a: a.name == key)
        ) is not None:
            return attr

        raise KeyError(f"'{key}' is not a valid sysfs attribute in {self.path}")

    def __setitem__(self, key, value):
        self[key].write(value)

    def __delitem__(self, key):
        del self.attributes[key]

    def __iter__(self):
        return iter(self.attributes)

    def __len__(self):
        return len(self.attributes)

    def pre(self) -> None:
        pass

    def post(self) -> None:
        pass

    def write_attr(self, attr: str, data: str | bytes) -> None:
        next(x for x in self.attributes if x.name == attr).write(data)

    def write_attr_bytes(self, attr: str, data: str) -> None:
        # TODO: This
        pass

    def read_attr_utf8(self, attr: str) -> str:
        return next(x for x in self.attributes if x.name == attr).read_utf8()

    def read_float(self, attr: str) -> float:
        """
        Read a sysfs attribute as a floating-point number

        Parameters
        ----------
        attr: str
            The sysfs attribute to read

        Returns
        -------
        The sysfs attribute as a floating-point number

        Raises
        ------
        SysFSError
            If the sysfs attribute does not exist
        ConversionError
            If the sysfs attribute could not be converted to a floating-point number
        """
        try:
            value = self.read_attr_utf8(attr)
            return float(value)
        except StopIteration as e:
            raise SysFSError(f"'{attr}' sysfs attribute does not exist") from e
        except SysFSError:
            raise
        except ValueError as e:
            raise ConversionError(
                "Failed to convert sysfs value to floating-point value"
            ) from e

    def read_int(self, attr) -> int:
        """
        Read a sysfs attribute stored as a string as an integer

        Parameters
        ----------
        attr: str
            The sysfs attribute to read

        Returns
        -------
        The sysfs attribute as an integer

        Raises
        ------
        SysFSError
            If the sysfs attribute does not exist
        ConversionError
            If the sysfs attribute could not be converted to an integer
        """
        try:
            value = self.read_attr_utf8(attr).strip()
            return int(value)
        except StopIteration as e:
            raise SysFSError(f"'{attr}' sysfs attribute does not exist") from e
        except SysFSError:
            raise
        except ValueError as e:
            raise ConversionError("Failed to convert sysfs value to int") from e

    def read_hex(self, attr) -> int:
        """
        Read a sysfs attribute stored as a hexadecimal integer as integer

        Parameters
        ----------
        attr: str
            The sysfs attribute to read

        Returns
        -------
        The sysfs attribute as a hexadecimal integer

        Raises
        ------
        SysFSError
            If the sysfs attribute does not exist
        ConversionError
            If the sysfs attribute could not be converted to a hexadecimal integer
        """
        try:
            value = self.read_attr_utf8(attr).strip()
            return int(value, 16)
        except StopIteration as e:
            raise SysFSError(f"'{attr}' sysfs attribute does not exist") from e
        except SysFSError:
            raise
        except ValueError as e:
            raise ConversionError("Failed to convert sysfs value to hex int") from e

    def read_utf8(self, attr, strip=True) -> str:
        """
        Read a sysfs attribute as a UTF-8 encoded string

        Parameters
        ----------
        attr: str
            The sysfs attribute to read
        strip: bool
            Strip whitespace, defaults to true

        Returns
        -------
        The sysfs attribute as a UTF-8 encoded string

        Raises
        ------
        SysFSError
            If the sysfs attribute does not exist
        """
        try:
            value = self.read_attr_utf8(attr)
            if strip:
                value = value.strip()

            return value
        except StopIteration as e:
            raise SysFSError(f"'{attr}' sysfs attribute does not exist") from e
        except SysFSError:
            raise

    def read_attr_bytes(self, attr: str) -> bytes:
        return next(x for x in self.attributes if x.name == attr).read_bytes()

    def read_bytes(self, attr) -> bytes:
        try:
            value = self.read_attr_bytes(attr)
            return value
        except StopIteration as e:
            raise SysFSError(f"'{attr}' sysfs attribute does not exist") from e
        except SysFSError:
            raise

    def extend_attributes(self, attributes: list[SysFSAttribute]):
        self.attributes.extend(attributes)

    def get_driver(self) -> str | None:
        path = self.path

        if self.path.joinpath("device").exists():
            path = self.path.joinpath("device")
        elif not path.joinpath("driver").exists():
            raise DriverError("Failed to retrieve driver info")

        return path.joinpath("driver").readlink().name
