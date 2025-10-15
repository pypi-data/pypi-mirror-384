from pathlib import Path
from typing import TYPE_CHECKING, Callable

from munch import Munch

from ekfsm.core.components import SysTree
from ekfsm.core.sysfs import SysfsDevice, sysfs_root
from ekfsm.exceptions import ConfigError, SysFSError, UnsupportedModeError

if TYPE_CHECKING:
    from ekfsm.core.components import HWModule


class Device(SysTree):
    """
    A generic device.
    """

    def __init__(
        self,
        name: str,
        parent: SysTree | None = None,
        children: list["Device"] | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(name, abort=abort)
        self.parent = parent
        self.device_args = kwargs

        if children:
            self.children = children

        # Needs to be set during init because root will be changed after tree is complete
        self.hw_module = self.root  # pyright: ignore[reportAttributeAccessIssue]

        # I2C initialization
        if not hasattr(self, "sysfs_device") or self.sysfs_device is None:
            self.sysfs_device: SysfsDevice | None = None

        # Post-initialization steps
        self._provides_attrs = kwargs.get("provides", {})
        self.provides = self.__post_init__(Munch(self._provides_attrs), abort)

    def __post_init__(self, provides: Munch, abort) -> Munch:
        for key, fields in provides.items():
            if isinstance(fields, dict):
                provides[key] = self.__post_init__(Munch(fields), abort)
            elif isinstance(fields, list | str):
                provides[key] = Munch()

                if isinstance(fields, str):
                    fields = [fields]

                while fields:
                    interface = fields.pop()

                    # TODO: Check if this is superfluous after schema validation
                    if isinstance(interface, dict):
                        name = list(interface.keys())[0]

                        try:
                            func = list(interface.values())[0]
                        except IndexError:
                            raise ConfigError(
                                f"{self.name}: No function given for interface {name}."
                            )

                        if not hasattr(self, func):
                            if abort:
                                raise NotImplementedError(
                                    f"{self.name}: Function {func} for interface {name} not implemented."
                                )
                            continue

                        provides[key].update({name: getattr(self, func)})
                    else:
                        if not hasattr(self, interface):
                            if abort:
                                raise NotImplementedError(
                                    f"{self.name}: Function {interface} for provider {key} not implemented."
                                )
                            continue

                        provides[key].update({interface: getattr(self, interface)})

        return provides

    @property
    def sysfs(self):
        """
        Access sysfs device for device

        Returns
        -------
        Sysfs device for device

        Raises
        ------
        SysFSError
            If the SysFSDevice does not exist
        """
        if self.sysfs_device is None:
            raise SysFSError(f"No sysfs device attached to device {self.name}")

        return self.sysfs_device

    def read_attr(self, attr: str, mode: str = "utf", strip: bool = True):
        match mode:
            case "utf":
                return self.sysfs.read_utf8(attr, strip)
            case "bytes":
                return self.sysfs.read_bytes(attr)
            case "float":
                return self.sysfs.read_float(attr)
            case "int":
                return self.sysfs.read_int(attr)
            case "hex":
                return self.sysfs.read_hex(attr)
            case _:
                raise UnsupportedModeError(f"Mode {mode} is not supported")

    def read_attr_or_default(
        self, attr: str, mode: str = "utf", strip: bool = True, default=None
    ):
        try:
            return self.read_attr(attr, mode, strip)
        except UnsupportedModeError:
            raise
        except Exception:
            if default is not None:
                return default
            return None

    def read_sysfs_bytes(self, attr) -> bytes:
        if len(attr) <= 0:
            raise SysFSError("sysfs attribute name too short")

        return self.sysfs.read_bytes(attr)

    def read_sysfs_attr_bytes(self, attr: str) -> bytes | None:
        """
        Read a sysfs attribute as bytes.

        Parameters
        ----------
        attr
            The sysfs attribute to read.

        Returns
        -------
        content: bytes
            The contents of the sysfs attribute as bytes.
        None:
            If the sysfs device is not set or the attribute does not exist.
        """
        if (
            self.sysfs_device is not None
            and len(attr) != 0
            and attr in [x.name for x in self.sysfs_device.attributes]
        ):
            return self.sysfs_device.read_attr_bytes(attr)
        return None

    def read_sysfs_attr_utf8(self, attr: str) -> str | None:
        """
        Read a sysfs attribute as UTF-8 string.

        Parameters
        ----------
        attr
            The sysfs attribute to read.

        Returns
        -------
        content: str
            The contents of the sysfs attribute as UTF-8 string.
        None:
            If the sysfs device is not set or the attribute does not exist.
        """
        try:
            return self.sysfs.read_utf8(attr)
        except Exception:
            return None

    def write_sysfs_attr(self, attr: str, data: str | bytes) -> None:
        """
        Write data to a sysfs attribute.

        Parameters
        ----------
        attr
            The sysfs attribute to write to.
        data
            The data to write to the sysfs attribute.
        """
        if self.sysfs_device and len(attr) != 0:
            return self.sysfs_device.write_attr(attr, data)
        return None

    @property
    def hw_module(self) -> "HWModule":
        """
        Get or set the HWModule instance that this device belongs to.

        Parameters
        ----------
        hw_module: optional
            The HWModule instance to set.

        Returns
        -------
        HWModule
            The HWModule instance that this device belongs to.
        None
            If used as a setter.
        """
        from ekfsm.core.components import HWModule

        if isinstance(self._hw_module, HWModule):
            return self._hw_module
        else:
            raise RuntimeError("Device is not a child of HWModule")

    @hw_module.setter
    def hw_module(self, hw_module: "HWModule") -> None:
        self._hw_module = hw_module

    def get_i2c_chip_addr(self) -> int:
        assert self.parent is not None

        chip_addr = self.device_args.get("addr")
        if chip_addr is None:
            raise ConfigError(
                f"{self.name}: Chip address not provided in board definition"
            )

        if not hasattr(self.parent, "sysfs_device") or self.parent.sysfs_device is None:
            # our device is the top level device of the slot
            # compute chip address from board yaml and slot attributes
            slot_attributes = self.hw_module.slot.attributes

            if slot_attributes is None:
                raise ConfigError(
                    f"{self.name}: Slot attributes not provided in system configuration"
                )

            if not self.hw_module.is_master:
                # slot coding is only used for non-master devices
                if not hasattr(slot_attributes, "slot_coding"):
                    raise ConfigError(
                        f"{self.name}: Slot coding not provided in slot attributes"
                    )

                slot_coding_mask = 0xFF

                if hasattr(slot_attributes, "slot_coding_mask"):
                    slot_coding_mask = slot_attributes.slot_coding_mask

                chip_addr |= slot_attributes.slot_coding & slot_coding_mask

        return chip_addr

    def get_i2c_sysfs_device(
        self, addr: int, driver_required=True, find_driver: Callable | None = None
    ) -> SysfsDevice:
        from ekfsm.core.components import HWModule

        parent = self.parent
        assert parent is not None

        # If parent is a HWModule, we can get the i2c bus from the master device
        # XXX: Does this still hold true after refactoring?
        if isinstance(parent, HWModule):
            i2c_bus_path = self.__master_i2c_bus()
        else:
            # otherwise the parent must be a MuxChannel
            from ekfsm.devices.mux import MuxChannel

            assert isinstance(parent, MuxChannel)
            assert parent.sysfs_device is not None
            i2c_bus_path = parent.sysfs_device.path

        # search for device with addr
        for entry in i2c_bus_path.iterdir():
            if (
                entry.is_dir()
                and not (entry / "new_device").exists()  # skip bus entries
                and (entry / "name").exists()
            ):
                # PRP devices unfortunately do not readily expose the underlying I2C address of the device like
                # regular I2C devices that follow the `${I2C_BUS}-${ADDR}` pattern. To address this issue, we
                # initialize the ACPI _STR object for each PRP device with the necessary information, which is
                # accessible in the `${DEVICE_SYSFS_PATH}/firmware_node/description` file.
                if (entry / "firmware_node").exists() and (
                    entry / "firmware_node" / "description"
                ).exists():
                    description = (
                        (entry / "firmware_node/description").read_text().strip()
                    )
                    acpi_addr = int(description.split(" - ")[0], 16)

                    if acpi_addr == addr:
                        return SysfsDevice(entry, driver_required, find_driver)

                # For regular non-PRP devices, the address is contained in the directory name (e.g. 2-0018).
                else:
                    acpi_addr = int(entry.name.split("-")[1], 16)

                    if acpi_addr == addr:
                        return SysfsDevice(entry, driver_required, find_driver)

        raise FileNotFoundError(
            f"Device with address 0x{addr:x} not found in {i2c_bus_path}"
        )

    @staticmethod
    def __master_i2c_get_config(master: "HWModule") -> dict:
        if (
            master.config.get("bus_masters") is not None
            and master.config["bus_masters"].get("i2c") is not None
        ):
            return master.config["bus_masters"]["i2c"]
        else:
            raise ConfigError("Master definition incomplete")

    def __master_i2c_bus(self) -> Path:
        if self.hw_module.is_master:
            # we are the master
            master = self.hw_module
            master_key = "MASTER_LOCAL_DEFAULT"
            override_master_key = self.device_args.get("i2c_master", None)

            if override_master_key is not None:
                master_key = override_master_key
        else:
            # another board is the master
            if self.hw_module.slot.master is None:
                raise ConfigError(
                    f"{self.name}: Master board not found in slot attributes"
                )

            master = self.hw_module.slot.master
            master_key = self.hw_module.slot.slot_type.name

        i2c_masters = self.__master_i2c_get_config(master)

        if i2c_masters.get(master_key) is not None:
            dir = sysfs_root() / Path(i2c_masters[master_key])
            bus_dirs = list(dir.glob("i2c-*"))

            if len(bus_dirs) == 1:
                return bus_dirs[0]
            elif len(bus_dirs) > 1:
                raise ConfigError(f"Multiple master I2C buses found for {master_key}")

            raise ConfigError(f"No master I2C bus found for {master_key}")
        else:
            raise ConfigError(f"Master I2C bus not found for {master_key}")

    def get_i2c_bus_number(self) -> int:
        """
        Get the I2C bus number of the device. Works for devices that do not have a sysfs_device attribute.
        """
        from ekfsm.devices.mux import MuxChannel

        if isinstance(self, MuxChannel):
            raise RuntimeError(f"{self.name}: MuxChannel does not have a bus number")

        if self.sysfs_device is None:
            if self.parent is None:
                raise RuntimeError(f"{self.name}: Must have a parent to get bus number")
            parent_path = self.parent.sysfs_device.path
        else:
            parent_path = self.sysfs_device.path.parent

        if parent_path.is_symlink():
            parent_path = parent_path.readlink()

        bus_number = parent_path.name.split("-")[1]

        return int(bus_number)

    def __repr__(self) -> str:
        sysfs_path = getattr(self.sysfs_device, "path", "")
        return f"{self.name}; Path: {sysfs_path}"
