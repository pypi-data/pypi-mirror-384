from abc import ABC, abstractmethod
from typing import List


class SimSMBus(ABC):
    @abstractmethod
    def read_word_data(self, cmd: int) -> int:
        pass

    @abstractmethod
    def read_block_data(self, cmd: int) -> List[int]:
        pass

    @abstractmethod
    def write_block_data(self, cmd: int, data: List[int]):
        pass

    @abstractmethod
    def write_byte(self, cmd: int):
        pass

    @abstractmethod
    def write_word_data(self, cmd: int, data: int):
        pass
