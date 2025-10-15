from typing import Callable
from ekfsm.devices.generic import Device
from ekfsm.log import ekfsm_logger

logger = ekfsm_logger(__name__)


class Button(Device):
    """
    Device class for handling a single button as part on array.
    """

    def __init__(
        self,
        name: str,
        parent: Device,
        children: list[Device] | None = None,
        abort: bool = False,
        channel_id: int = 0,
        *args,
        **kwargs,
    ):
        logger.debug(f"Initializing Button '{name}' on channel {channel_id}")

        super().__init__(name, parent, children, abort, *args, **kwargs)

        self.channel_id = channel_id
        logger.debug(f"Button '{name}' assigned to channel {channel_id}")

        self._handler: Callable | None = None
        logger.info(f"Button '{name}' initialized on channel {channel_id}")

    @property
    def handler(self):
        """
        Handle button events with a callback function.
        """
        return self._handler

    @handler.setter
    def handler(self, func: Callable | None, *args, **kwargs):
        """
        Handle button events with a callback function.

        Parameters
        ----------
        func : Callable | None
            The function to call on button events. If None, no function is called.
        """
        if callable(func):
            self._handler = func
            logger.info(
                f"Handler set for button '{self.name}' on channel {self.channel_id}"
            )
            logger.debug(
                f"Handler function: {func.__name__ if hasattr(func, '__name__') else str(func)}"
            )
        else:
            self._handler = None
            logger.debug(
                f"Handler cleared for button '{self.name}' on channel {self.channel_id}"
            )

    def __repr__(self):
        return f"{self.name}; Channel ID: {self.channel_id}"
