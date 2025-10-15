from ekfsm.devices.generic import Device
from ekfsm.devices.io4edge import IO4Edge
from ekfsm.log import ekfsm_logger
from io4edge_client.analogintypeb import Client

logger = ekfsm_logger(__name__)


class ThermalHumidity(Device):
    """
    Device class for handling a thermal humidity sensor.
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
            f"Initializing ThermalHumidity sensor '{name}' with parent device {parent.deviceId}"
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
            f"ThermalHumidity '{name}' configured with service address: {self.service_addr}"
        )

        try:
            self.client = Client(self.service_addr, connect=False)
            logger.debug(
                f"ThermalHumidity client created for service: {self.service_addr}"
            )
        except Exception as e:
            logger.error(
                f"Failed to create ThermalHumidity client for {self.service_addr}: {e}"
            )
            raise

    def temperature(self) -> float:
        """
        Get the temperature in Celsius.

        Raises
        ------
        RuntimeError
            if the command fails
        TimeoutError
            if the command times out
        """
        logger.debug(f"Reading temperature from ThermalHumidity sensor '{self.name}'")
        try:
            temp = self.client.value()
            logger.debug(f"ThermalHumidity '{self.name}' temperature: {temp}°C")
            return temp
        except Exception as e:
            logger.error(
                f"Failed to read temperature from ThermalHumidity '{self.name}': {e}"
            )
            raise

    def __repr__(self):
        return f"{self.name}; Service Address: {self.service_addr}"
