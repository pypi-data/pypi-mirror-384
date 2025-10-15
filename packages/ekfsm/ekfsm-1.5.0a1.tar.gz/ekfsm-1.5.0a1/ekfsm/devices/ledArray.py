from ekfsm.devices.generic import Device
from ekfsm.devices.io4edge import IO4Edge
from ekfsm.log import ekfsm_logger
from io4edge_client.colorLED import Client

logger = ekfsm_logger(__name__)


class LEDArray(Device):
    """
    Device class for handling a LED array.
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
            f"Initializing LEDArray '{name}' with parent device {parent.deviceId}"
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
            f"LEDArray '{name}' configured with service address: {self.service_addr}"
        )

        try:
            self.client = Client(self.service_addr)
            logger.debug(f"LEDArray client created for service: {self.service_addr}")
        except Exception as e:
            logger.error(
                f"Failed to create LEDArray client for {self.service_addr}: {e}"
            )
            raise

    def __repr__(self):
        return f"{self.name}; Service Address: {self.service_addr}"
