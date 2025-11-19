from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.server import StartSerialServer, ModbusSerialServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext, ModbusServerContext
from pymodbus import ModbusDeviceIdentification
from pymodbus.framer import FramerRTU
import asyncio

if __name__ == "__main__":
    client = ModbusSerialClient(
        port='COM4',
        baudrate=500000,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=0.5
    )

    if not client.connect():
        print("Failed to connect to the serial port.")
        exit()

    found_devices = []
    for unit_id in [0x01, 0x02, 0x03, 0x04, 0x05, 0x55]:  # Modbus addresses typically range from 1 to 247
        try:
            print(f'Trying to read {unit_id=}')
            # Attempt to read a register (e.g., holding register 0)
            # This is a common way to check for a device's presence.
            response = client.read_holding_registers(address=0x2000, count=1, device_id=unit_id)

            if not response.isError():
                print(f"Device found at Unit ID: {unit_id}")
                found_devices.append(unit_id)
            else:
                print(response)
                # Handle specific Modbus errors if needed, e.g., no response
                pass
        except ModbusIOException as e:
            # This exception might occur if the device is not present or not responding
            pass
        except Exception as e:
            print(f"An unexpected error occurred for Unit ID {unit_id}: {e}")

    client.close()
    print(f"Scan complete. Found devices at Unit IDs: {found_devices}")