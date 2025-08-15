import threading
import queue
from pymodbus.exceptions import ConnectionException
from pymodbus.client import ModbusSerialClient as ModbusClient
from OM_comm_interface import *
import struct
from loguru import logger
import time


def PackToRegisters(pack:list = []):
    if len(pack) % 2 != 0:
        pack.append(0x00)    
    registers = [((pack[i+1] << 8) | (pack[i])) for i in range(0, len(pack), 2)]
    return registers

# Reversed func: turns registers to array of bytes
def RegistersToPack(registers: list = []):
    # pack = []
    # for reg in registers:
    #     pack.append(reg & 0xFF)
    #     pack.append((reg >> 8) & 0xFF)
    # Use of struct.pack needed
    pack = []
    for reg in registers:
        pack.extend(struct.pack(">H", reg))
        
    return pack
    

class ModbusWorker(threading.Thread, OMCommInterface):
    def __init__(self, port, baudrate, stopbits, parity, bytesize, timeout=1):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.stopbits = stopbits
        self.parity = parity
        self.bytesize = bytesize
        self.timeout = timeout
        self.request_queue = queue.Queue(maxsize=100)
        self.response_queue = queue.Queue()
        self.running = False
        self.client : ModbusClient = ModbusClient(
                port=self.port,
                baudrate=self.baudrate,
                stopbits=self.stopbits,
                parity=self.parity,
                bytesize=self.bytesize,
                timeout=self.timeout,
            )

    def connect(self):
        try:

            self.client.connect()
            logger.info(f"Connected to Modbus on {self.port}")
            return True
        except ConnectionException as e:
            print(f"Failed to connect to Modbus: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info(f"Disconnected from Modbus on {self.port}")

    # def run(self):
    #     if not self.connect():
    #         return

    #     self.running = True
    #     while self.running:
    #         try:
    #             request = self.request_queue.get(timeout=1)
    #             if request is None:
    #                 continue
    #             logger.debug(f"Processing request: {request.__dict__}")
    #             response = self.handle_request(request)
    #             logger.debug(f"Received response: {response}")
    #             self.response_queue.put(response)
    #         except queue.Empty:
    #             pass

    #     self.disconnect()

    def stop(self):
        self.running = False
        self.request_queue.put(None)
        self.join()

    def handle_request(self, request, silent=False):
        if request.type == ModbusRequestType.READ:
            if not silent:
                logger.debug(f"Sending READ request to address {request.address}, count {request.count}, slave {request.slave_id}")
            try:
                result = self.client.read_holding_registers(
                    request.address, count=request.count, device_id=request.slave_id
                )
                if result.isError():
                    return {"error": str(result)}
                return {"data": result.registers}
            except Exception as e:
                return {"error": str(e)}
        elif request.type == ModbusRequestType.WRITE_MULTY:
            if not silent:
                logger.debug(f"Sending WRITE request to address {request.address}, value {request.registers}, slave {request.slave_id}")
            try:
                result = self.client.write_registers(
                    request.address, request.registers, device_id=request.slave_id
                )
                if result.isError():
                    return {"error": str(result)}
                return {"status": "success"}
            except Exception as e:
                return {"error": str(e)}
        elif request.type == ModbusRequestType.WRITE_SINGLE:
            logger.error("Unsupported!")
            return {"error": "Unsupported"}
        else:
            logger.error(f"Unknown request type: {request.type}")
            return {"error": "Unknown request type"}

    def send_request(self, request, blocking=True, timeout=5, silent=False):
        self.request_queue.put((request, silent))
        if blocking:
            start_time = time.time()
            while True:
                try:
                    response: dict[str, str] = self.response_queue.get(timeout=0.1)
                    return response
                except queue.Empty:
                    if time.time() - start_time > timeout:
                        logger.warning(f"Request timed out after {timeout} seconds")
                        return {"error": "Timeout"}
        else:
            return None

    def run(self):
        if not self.connect():
            return

        self.running = True
        while self.running:
            try:
                item = self.request_queue.get(timeout=1)
                if item is None:
                    continue
                if isinstance(item, tuple):
                    request, silent = item
                else:
                    request, silent = item, False
                if not silent:
                    logger.debug(f"Processing request: {request.__dict__}")
                response = self.handle_request(request, silent=silent)
                if not silent:
                    logger.debug(f"Received response: {response}")
                self.response_queue.put(response)
            except queue.Empty:
                pass

        self.disconnect()