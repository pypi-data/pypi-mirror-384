from ekfsm.devices.generic import Device
from ekfsm.devices.io4edge import IO4Edge
from ekfsm.log import ekfsm_logger
from io4edge_client.watchdog import Client

logger = ekfsm_logger(__name__)


class Watchdog(Device):
    """
    Device class for handling an application watchdog.
    """

    def __init__(
        self,
        name: str,
        parent: IO4Edge,
        children: list[Device] | None = None,
        abort: bool = False,
        service_suffix: str | None = None,
        *args,
        **kwargs,
    ):
        logger.debug(
            f"Initializing Watchdog '{name}' with parent device {parent.deviceId}"
        )

        super().__init__(name, parent, children, abort, *args, **kwargs)

        self.name = name

        if service_suffix is not None:
            self.service_suffix = service_suffix
            logger.debug(f"Using custom service suffix: {service_suffix}")
        else:
            self.service_suffix = name
            logger.debug(f"Using default service suffix: {name}")

        self.service_addr = f"{parent.deviceId}-{self.service_suffix}"
        logger.info(
            f"Watchdog '{name}' configured with service address: {self.service_addr}"
        )

        try:
            self.client = Client(self.service_addr, connect=False)
            logger.debug(f"Watchdog client created for service: {self.service_addr}")
        except Exception as e:
            logger.error(
                f"Failed to create Watchdog client for {self.service_addr}: {e}"
            )
            raise

    def describe(self):
        pass

    def kick(self) -> None:
        """
        Kick the watchdog.

        Raises
        ------
        RuntimeError
            if the command fails
        TimeoutError
            if the command times out
        """
        logger.debug(f"Kicking watchdog '{self.name}' on service {self.service_addr}")
        try:
            self.client.kick()
            logger.debug(f"Watchdog '{self.name}' kick successful")
        except Exception as e:
            logger.error(f"Failed to kick watchdog '{self.name}': {e}")
            raise

    def __repr__(self):
        return f"{self.name}; Service Address: {self.service_addr}"
