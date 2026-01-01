import threading
import queue
import time
import asyncio
from loguru import logger
from OM_comm_interface import OMCommInterface, ModbusRequest, ModbusRequestType
from usb_can_driver.usb_can import USB_CAN_Driver
from usb_can_driver.canv_structs import IVar


class MBOverCANWorker(threading.Thread, OMCommInterface):
    def __init__(self, can_driver: USB_CAN_Driver, dev_id=4, port_to_use=0, can_timeout=0.1):
        super().__init__()
        self.can_driver = can_driver
        self.dev_id = dev_id
        self.port_to_use = port_to_use
        self.can_timeout = can_timeout
        self.request_queue = queue.Queue(maxsize=100)
        self.response_queue = queue.Queue()
        self.running = False
        self.loop = None
        self.var_id = 9  # Fixed IVar for Modbus-over-CAN

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.running = True
        logger.info("MB-over-CAN worker started")

        while self.running:
            try:
                item = self.request_queue.get(timeout=1)
                if item is None:
                    continue
                request, silent = item if isinstance(item, tuple) else (item, False)

                if not silent:
                    logger.debug(f"Processing CAN request: {request.__dict__}")

                response = self.handle_request(request, silent=silent)

                if not silent:
                    logger.debug(f"CAN response: {response}")

                self.response_queue.put(response)

            except queue.Empty:
                continue
            except Exception as e:
                logger.exception("MB-over-CAN worker error")

        logger.info("MB-over-CAN worker stopped")

    def handle_request(self, request: ModbusRequest, silent=False):
        try:
            if request.type == ModbusRequestType.READ:
                # Build command frame
                payload = bytearray([
                    0,  # exec status (dummy)
                    self.port_to_use,
                    0x03,  # Function code: read holding registers
                    request.slave_id,
                    request.address & 0xFF,
                    (request.address >> 8) & 0xFF,
                    request.count & 0xFF,
                    (request.count >> 8) & 0xFF,
                ])
                ivar = IVar(self.dev_id, self.var_id, 0)
                # Send command
                asyncio.run(self.can_driver.write(ivar, payload))
                time.sleep(self.can_timeout)

                # Read response (8-byte header + 2 * count)
                data = asyncio.run(self.can_driver.read(ivar, d_len=8 + 2 * request.count))
                if len(data) < 8 + 2 * request.count:
                    return {"error": "Incomplete read response"}

                # Parse registers (big-endian)
                registers = []
                for i in range(request.count):
                    reg = int.from_bytes(data[8 + i*2: 8 + i*2 + 2], "big")
                    registers.append(reg)
                return {"data": registers}

            elif request.type == ModbusRequestType.WRITE_MULTY:
                # First: send data payload
                data_bytes = b"".join(reg.to_bytes(2, "big") for reg in request.registers)
                ivar_data = IVar(self.dev_id, self.var_id, 8)
                asyncio.run(self.can_driver.write(ivar_data, data_bytes))
                time.sleep(self.can_timeout)

                # Then: send command header
                payload = bytearray([
                    0,  # exec status
                    self.port_to_use,
                    0x10,  # Function code: write multiple registers
                    request.slave_id,
                    request.address & 0xFF,
                    (request.address >> 8) & 0xFF,
                    len(request.registers) & 0xFF,
                    (len(request.registers) >> 8) & 0xFF,
                ])
                ivar_cmd = IVar(self.dev_id, self.var_id, 0)
                asyncio.run(self.can_driver.write(ivar_cmd, payload))
                return {"status": "success"}

            else:
                return {"error": "Unsupported request type"}

        except Exception as e:
            return {"error": f"CAN request failed: {str(e)}"}

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

        logger.warning("CAN request timed out")
        return {"error": "Timeout"}

    def stop(self):
        self.running = False
        self.request_queue.put(None)
        self.join()
        if self.loop and self.loop.is_running():
            self.loop.stop()
        logger.info("MB-over-CAN worker stopped")
