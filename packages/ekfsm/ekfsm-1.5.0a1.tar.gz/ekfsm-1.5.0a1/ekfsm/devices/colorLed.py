from ekfsm.devices.generic import Device
from ekfsm.devices.ledArray import LEDArray
from ekfsm.log import ekfsm_logger
from io4edge_client.api.colorLED.python.colorLED.v1alpha1.colorLED_pb2 import Color

logger = ekfsm_logger(__name__)


class ColorLED(Device):
    """
    Device class for handling a color LED.
    """

    def __init__(
        self,
        name: str,
        parent: LEDArray,
        children: list[Device] | None = None,
        abort: bool = False,
        channel_id: int = 0,
        *args,
        **kwargs,
    ):
        logger.debug(f"Initializing ColorLED '{name}' on channel {channel_id}")

        super().__init__(name, parent, children, abort, *args, **kwargs)

        self.name = name
        self.channel_id = channel_id

        self.client = parent.client
        logger.info(
            f"ColorLED '{name}' initialized on channel {channel_id} with parent LEDArray"
        )

    def describe(self):
        pass

    def get(self) -> tuple[Color, bool]:
        """
        Get color LED state.

        Returns
        -------
            Current color and blink state.

        Raises
        ------
        RuntimeError
            if the command fails
        TimeoutError
            if the command times out
        """
        logger.debug(
            f"Getting color LED state for '{self.name}' on channel {self.channel_id}"
        )
        try:
            result = self.client.get(self.channel_id)
            color, blink = result
            logger.debug(f"ColorLED '{self.name}' state: color={color}, blink={blink}")
            return result
        except Exception as e:
            logger.error(
                f"Failed to get ColorLED '{self.name}' state on channel {self.channel_id}: {e}"
            )
            raise

    def set(self, color: Color, blink: bool) -> None:
        """
        Set the color of the color LED.

        Parameters
        ----------
        color : Color
            The color to set the LED to.
        blink : bool
            Whether to blink the LED.

        Raises
        ------
        RuntimeError
            if the command fails
        TimeoutError
            if the command times out
        """
        logger.info(
            f"Setting ColorLED '{self.name}' on channel {self.channel_id}: color={color}, blink={blink}"
        )
        try:
            self.client.set(self.channel_id, color, blink)
            logger.debug(
                f"ColorLED '{self.name}' successfully set to color={color}, blink={blink}"
            )
        except Exception as e:
            logger.error(
                f"Failed to set ColorLED '{self.name}' on channel {self.channel_id}: {e}"
            )
            raise

        def __repr__(self):
            return f"{self.name}; Channel ID: {self.channel_id}"
