from crcmod.predefined import Crc


def get_crc16_xmodem(data: bytes) -> int:
    crc16_xmodem = Crc("xmodem")
    crc16_xmodem.update(data)
    return crc16_xmodem.crcValue
