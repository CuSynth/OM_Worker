import threading
import queue
from pymodbus.exceptions import ConnectionException
from pymodbus.client import ModbusSerialClient as ModbusClient
from OM_comm_interface import *
import struct
from loguru import logger
import time


def PackToRegisters(pack: list) -> list:
    if len(pack) % 2 != 0:
        pack.append(0x00)
    return [((pack[i+1] << 8) | pack[i]) for i in range(0, len(pack), 2)]


# Reversed func: turns registers to array of bytes
def RegistersToPack(registers: list) -> bytes:
    data = b""
    for reg in registers:
        data += struct.pack(">H", reg)
    return data
    

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
        self.client = ModbusClient(
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
            logger.info(f"Modbus RTU connected: {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect Modbus: {e}")
            return False


    def disconnect(self):
        if self.client and self.client.socket:
            self.client.close()
            logger.info("Modbus RTU disconnected")

    def run(self):
        if not self.connect():
            return
        self.running = True

        while self.running:
            try:
                item = self.request_queue.get(timeout=1)
                if item is None:
                    continue
                request, silent = item if isinstance(item, tuple) else (item, False)

                if not silent:
                    logger.debug(f"Processing request: {request.__dict__}")

                response = self.handle_request(request, silent=silent)

                if not silent:
                    logger.debug(f"Response: {response}")

                self.response_queue.put(response)

            except queue.Empty:
                continue
            except KeyboardInterrupt:
                logger.warning(f"{self.__class__.__name__} caught KeyboardInterrupt. Stopping gracefully.")
                self.running = False
                break
            except Exception as e:
                logger.exception(f"{self.__class__.__name__} error: {e}")


        self.disconnect()

    def handle_request(self, request, silent=False):
        try:
            if request.type == ModbusRequestType.READ:
                result = self.client.read_holding_registers(
                    address=request.address,
                    count=request.count,
                    device_id=request.slave_id
                )
                if result.isError():
                    return {"error": str(result)}
                return {"data": result.registers}

            elif request.type == ModbusRequestType.WRITE_MULTY:
                result = self.client.write_registers(
                    address=request.address, 
                    values=request.registers, 
                    device_id=request.slave_id
                )
                
                if result.isError():
                    return {"error": str(result)}
                return {"status": "success"}

            elif request.type == ModbusRequestType.WRITE_SINGLE:
                # Optional: support if needed
                return {"error": "WRITE_SINGLE not supported"}

            else:
                return {"error": "Unknown request type"}

        except Exception as e:
            return {"error": f"Exception: {str(e)}"}

    def send_request(self, request, blocking=True, timeout=5, silent=False):
        self.request_queue.put((request, silent))

        if not blocking:
            return None

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return self.response_queue.get(timeout=0.1)
            except queue.Empty:
                continue

        logger.warning("Request timed out")
        return {"error": "Timeout"}

    def stop(self):
        self.running = False
        self.request_queue.put(None)
        self.join()