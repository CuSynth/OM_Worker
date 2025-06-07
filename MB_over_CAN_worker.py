from OM_comm_interface import *
import threading
import queue
import time
import asyncio
from usb_can_driver.usb_can import USB_CAN_Driver
from usb_can_driver.canv_structs import IVar

class MBOverCANWorker(threading.Thread, OMCommInterface):
    def __init__(self, can_driver, dev_id=4, port_to_use=0):
        super().__init__()
        self.can_driver = can_driver
        self.dev_id = dev_id
        self.port_to_use = port_to_use
        self.request_queue = queue.Queue(maxsize=100)
        self.response_queue = queue.Queue()
        self.running = False
        self.loop = None

    def send_request(self, request, blocking=True, timeout=5, silent=False):
        self.request_queue.put((request, silent))
        if blocking:
            start_time = time.time()
            while True:
                try:
                    response = self.response_queue.get(timeout=0.1)
                    return response
                except queue.Empty:
                    if time.time() - start_time > timeout:
                        return {"error": "Timeout"}
        else:
            return None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
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
                response = self.handle_request(request, silent=silent)
                self.response_queue.put(response)
            except queue.Empty:
                pass

    def stop(self):
        self.running = False
        self.request_queue.put(None)
        self.join()
        if self.loop:
            self.loop.close()

    def handle_request(self, request, silent=False):
        var_id = 9

        if request.type == ModbusRequestType.READ:
            # Build payload for Modbus-over-CAN read
            payload = bytearray([
                0,  # exec status (dummy)
                self.port_to_use,
                0x03,  # FCode for read
                request.slave_id,
                request.address & 0xFF,
                (request.address >> 8) & 0xFF,
                request.count & 0xFF,
                (request.count >> 8) & 0xFF,
            ])
            ivar = IVar(self.dev_id, var_id, 0)
            # Write config to CAN (async)
            asyncio.run(self.can_driver.write(ivar, payload))
            # Read back data (async)
            time.sleep(0.05)
            data = asyncio.run(self.can_driver.read(ivar, d_len=8 + request.count * 2))
            # Parse data field (skip first 8 bytes)
            return {"data": [int.from_bytes(data[8+i*2:8+i*2+2], "big") for i in range(request.count)]}
        elif request.type == ModbusRequestType.WRITE_MULTY:
            # Build payload for Modbus-over-CAN write
            data_bytes = bytearray()
            for reg in request.registers:
                data_bytes += reg.to_bytes(2, "big")
            payload = data_bytes
            ivar = IVar(self.dev_id, var_id, 8)
            asyncio.run(self.can_driver.write(ivar, payload))
            # Command/config write: only config, no data
            payload_cmd = bytearray([
                0,  # exec status (dummy)
                self.port_to_use,
                0x10,  # FCode for write
                request.slave_id,
                request.address & 0xFF,
                (request.address >> 8) & 0xFF,
                len(request.registers) & 0xFF,
                (len(request.registers) >> 8) & 0xFF,
            ])
            ivar = IVar(self.dev_id, var_id, 0)
            asyncio.run(self.can_driver.write(ivar, payload_cmd))
            return {"status": "success"}
        else:
            return {"error": "Unsupported request type"}
        

async def main(dev):
    start = time.time()
    for _ in range(10):
        print("Running..")
        print((await dev.read(IVar(4, 5, 0), 128)).hex(' ').upper())
    print(f'{time.time() - start:.3f}')

async def write_mb_over_can(dev):
    dev_id = 4
    var_id = 9
    offset = 0
    registers = [0x0021]
    data_bytes = bytearray()
    for reg in registers:
        data_bytes += reg.to_bytes(2, "little")
    payload = bytearray([
        0,  # exec status (dummy)
        0,
        0x10,  # FCode for write
        0x02,
        (0x1000 >> 8) & 0xFF,
        0x1000 & 0xFF,
        (len(registers) >> 8) & 0xFF,
        len(registers) & 0xFF
    ]) + data_bytes
    ivar = IVar(dev_id, var_id, offset)

    print(await dev.write(ivar, payload))

if __name__ == '__main__':
    # Simple example to read dev=4, var=5, off=0, len=128 
    driver = USB_CAN_Driver()
    driver.connect("COM5")
    asyncio.run(main(driver))