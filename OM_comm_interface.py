from abc import ABC, abstractmethod
from enum import Enum

class OMCommInterface(ABC):
    @abstractmethod
    def send_request(self, request, blocking=True, timeout=5, silent=False):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass


class ModbusRequestType(Enum):
    READ = 1
    WRITE_SINGLE = 2
    WRITE_MULTY = 3

class ModbusRequest:
    def __init__(self, type: ModbusRequestType, address: int, count: int = 0, registers: list =[], slave_id: int = 1):
        self.type = type
        self.address = address
        self.count = count
        self.registers = registers
        self.slave_id = slave_id

