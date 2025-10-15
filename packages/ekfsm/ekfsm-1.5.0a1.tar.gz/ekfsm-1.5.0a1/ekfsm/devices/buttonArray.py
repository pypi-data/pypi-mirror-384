import threading
from ekfsm.devices.button import Button
from ekfsm.devices.generic import Device
from ekfsm.devices.io4edge import IO4Edge
from ekfsm.log import ekfsm_logger
from io4edge_client.binaryiotypeb import Client, Pb
import io4edge_client.functionblock as fb

logger = ekfsm_logger(__name__)


class ButtonArray(Device):
    """
    Device class for handling an io4edge button array.

    To read button events, call the `read` method in a separate thread.

    Note
    ----
        Button handlers are called in the context of the `read` method's thread and need to be set in the Button instances.
    """

    def __init__(
        self,
        name: str,
        parent: IO4Edge,
        children: list[Device] | None = None,
        abort: bool = False,
        service_suffix: str | None = None,
        keepaliveInterval: int = 10000,
        *args,
        **kwargs,
    ):
        logger.debug(
            f"Initializing ButtonArray '{name}' with parent device {parent.deviceId}"
        )

        Device.__init__(self, name, parent, children, abort, *args, **kwargs)

        self.name = name

        if service_suffix is not None:
            self.service_suffix = service_suffix
            logger.debug(f"Using custom service suffix: {service_suffix}")
        else:
            self.service_suffix = name
            logger.debug(f"Using default service suffix: {name}")

        self.service_addr = f"{parent.deviceId}-{self.service_suffix}"
        self.timeout = keepaliveInterval / 1000 + 5

        logger.info(
            f"ButtonArray '{name}' configured with service address: {self.service_addr}"
        )
        logger.debug(
            f"Keepalive interval: {keepaliveInterval}ms, timeout: {self.timeout}s"
        )

        try:
            self.client = Client(
                self.service_addr, command_timeout=self.timeout, connect=False
            )
            logger.debug(f"IO4Edge client created for service: {self.service_addr}")
        except Exception as e:
            logger.error(
                f"Failed to create IO4Edge client for {self.service_addr}: {e}"
            )
            raise

        self.subscriptionType = Pb.SubscriptionType.BINARYIOTYPEB_ON_RISING_EDGE
        self.stream_cfg = fb.Pb.StreamControlStart(
            bucketSamples=1,  # 1 sample per bucket, also ein event pro bucket
            keepaliveInterval=keepaliveInterval,
            bufferedSamples=2,  # 2 samples werden gepuffert
            low_latency_mode=True,  # schickt soweit moeglich sofort die Events
        )
        logger.debug(
            "Stream configuration initialized with rising edge subscription and low latency mode"
        )

        # Log button children count
        button_count = sum(1 for child in (children or []) if isinstance(child, Button))
        logger.info(f"ButtonArray '{name}' initialized with {button_count} button(s)")

    def read(self, stop_event: threading.Event | None = None, timeout: float = 1):
        """
        Read all button events and dispatch to handlers.

        Parameters
        ----------
        stop_event : threading.Event, optional
            Event to signal stopping the reading loop. If None, the loop will run indefinitely.
        timeout : float, optional
            Timeout for reading from the stream in seconds. Default is 0.1 seconds.

        Note
        ----
            This method blocks and should be run in a separate thread.
        """
        button_channels = [
            button for button in self.children if isinstance(button, Button)
        ]

        if not button_channels:
            logger.warning(
                f"No button children found in ButtonArray '{self.name}', read operation will have no effect"
            )
            return

        logger.info(
            f"Starting button event reading for {len(button_channels)} buttons on '{self.name}'"
        )
        logger.debug(
            f"Read timeout: {timeout}s, stop_event provided: {stop_event is not None}"
        )

        try:
            with self.client as client:
                logger.debug(
                    f"IO4Edge client connected to service: {self.service_addr}"
                )

                # Prepare subscription channels
                subscribe_channels = tuple(
                    Pb.SubscribeChannel(
                        channel=button.channel_id,
                        subscriptionType=self.subscriptionType,
                    )
                    for button in button_channels
                )

                channel_ids = [button.channel_id for button in button_channels]
                logger.debug(
                    f"Subscribing to {len(subscribe_channels)} button channels: {channel_ids}"
                )

                client.start_stream(
                    Pb.StreamControlStart(subscribeChannel=subscribe_channels),
                    self.stream_cfg,
                )
                logger.info(
                    f"Button event stream started for ButtonArray '{self.name}'"
                )

                event_count = 0
                try:
                    while not (stop_event and stop_event.is_set()):
                        try:
                            _, samples = client.read_stream(timeout=timeout)

                            for sample in samples.samples:
                                for button in button_channels:
                                    pressed = bool(
                                        sample.inputs & (1 << button.channel_id)
                                    )
                                    if pressed:
                                        event_count += 1
                                        button_name = getattr(button, "name", "unnamed")
                                        logger.debug(
                                            f"Button press on channel {button.channel_id} ({button_name})"
                                        )

                                        if button.handler:
                                            try:
                                                logger.debug(
                                                    f"Calling handler for button on channel {button.channel_id}"
                                                )
                                                button.handler()
                                            except Exception as e:
                                                logger.error(
                                                    f"Error in button handler for channel {button.channel_id}: {e}"
                                                )
                                        else:
                                            logger.debug(
                                                f"No handler set for button on channel {button.channel_id}"
                                            )

                        except TimeoutError:
                            # Timeout is expected during normal operation
                            continue
                        except Exception as e:
                            logger.error(
                                f"Error reading button events from stream: {e}"
                            )
                            break

                except KeyboardInterrupt:
                    logger.info(
                        f"Button reading interrupted for ButtonArray '{self.name}'"
                    )
                finally:
                    logger.info(
                        f"Button event reading stopped for '{self.name}' after processing {event_count} events"
                    )
                    if stop_event:
                        stop_event.clear()
                        logger.debug("Stop event cleared")

        except Exception as e:
            logger.error(
                f"Failed to establish connection or start stream for ButtonArray '{self.name}': {e}"
            )
            raise

    def __repr__(self):
        return f"{self.name}; Service Address: {self.service_addr}"
