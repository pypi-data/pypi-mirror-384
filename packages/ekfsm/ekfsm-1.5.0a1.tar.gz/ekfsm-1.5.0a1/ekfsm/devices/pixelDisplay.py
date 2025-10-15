from ekfsm.devices.generic import Device
from ekfsm.devices.io4edge import IO4Edge
from ekfsm.log import ekfsm_logger
from io4edge_client.pixelDisplay import Client
from PIL import Image

logger = ekfsm_logger(__name__)


class PixelDisplay(Device):
    """
    Device class for handling a pixel display.
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
            f"Initializing PixelDisplay '{name}' with parent device {parent.deviceId}"
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
            f"PixelDisplay '{name}' configured with service address: {self.service_addr}"
        )

        try:
            self.client = Client(self.service_addr, connect=False)
            logger.debug(
                f"PixelDisplay client created for service: {self.service_addr}"
            )
        except Exception as e:
            logger.error(
                f"Failed to create PixelDisplay client for {self.service_addr}: {e}"
            )
            raise

    def describe(self) -> dict:
        """
        Returns a description of the pixel display.
        """
        logger.debug(f"Getting PixelDisplay description for '{self.name}'")
        try:
            describe = self.client.describe()
            desc = {
                "height": describe.height_pixel,
                "width": describe.width_pixel,
                "max_num_of_pixel": describe.max_num_of_pixel,
            }
            logger.debug(f"PixelDisplay '{self.name}' description: {desc}")
            return desc
        except Exception as e:
            logger.error(
                f"Failed to get PixelDisplay description for '{self.name}': {e}"
            )
            raise

    @property
    def height(self) -> int:
        """
        Returns the height of the pixel display in pixels.
        """
        return self.describe()["height"]

    @property
    def width(self) -> int:
        """
        Returns the width of the pixel display in pixels.
        """
        return self.describe()["width"]

    def off(self) -> None:
        """
        Turn off the pixel display.
        @raises RuntimeError: if the command fails
        @raises TimeoutError: if the command times out
        """
        logger.info(f"Turning off PixelDisplay '{self.name}'")
        try:
            self.client.set_display_off()
            logger.debug(f"PixelDisplay '{self.name}' successfully turned off")
        except Exception as e:
            logger.error(f"Failed to turn off PixelDisplay '{self.name}': {e}")
            raise

    def display_image(self, path: str) -> None:
        """
        Display an image on the pixel display.
        @raises RuntimeError: if the command fails
        @raises TimeoutError: if the command times out
        """
        logger.info(f"Displaying image '{path}' on PixelDisplay '{self.name}'")
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                pix = img.load()
                logger.debug(
                    f"Image '{path}' loaded and converted to RGB for PixelDisplay '{self.name}'"
                )

            with self.client as client:
                logger.debug(f"Sending pixel data to PixelDisplay '{self.name}'")
                for i in range(0, 320, 16):
                    pix_area = []
                    for k in range(0, 16):
                        for j in range(0, 240):
                            pix_area.append(pix[j, i + k])
                    client.set_pixel_area(0, i, 239, pix_area)
                logger.debug(
                    f"Image successfully displayed on PixelDisplay '{self.name}'"
                )
        except Exception as e:
            logger.error(
                f"Failed to display image '{path}' on PixelDisplay '{self.name}': {e}"
            )
            raise

    def __repr__(self):
        return f"{self.name}; Service Address: {self.service_addr}"
