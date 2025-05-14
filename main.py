from OM_worker_base import *
from loguru import logger


SLAVE_ADDR  = 2
COMM_PORT   = "COM9"
BAUDRATE    = 500000



# Example Usagepymodbus
if __name__ == "__main__":
    logger.add("logs/app.log", level="DEBUG", rotation="500 KB", retention="1 week")
    logger.info("Application started")
    try:
        modbus_worker = ModbusWorker(
            port=COMM_PORT, baudrate=BAUDRATE, stopbits=1, parity="N", bytesize=8
        )
        OM_entry = OM_Interface(modbus_worker, slave_id=SLAVE_ADDR)

        modbus_worker.start()
        time.sleep(0.1)
        logger.info("Modbus worker started")


# ---
# SS data example
        # for i in range(5):
        #     logger.info(f"Iteration {i+1}")
        #     take_data_result = OM_entry.SS_take_data()
        #     logger.debug(f"SS_take_data result: {take_data_result}")
        #     read_data_result = OM_entry.SS_read_data()
        #     logger.debug(f"SS_read_data result: {read_data_result}")
        #     time.sleep(1)
# ---
# Set/Get DevID example
        # take_data_result = OM_entry.SS_take_data()
        # logger.debug(f"SS_take_data result: {take_data_result}")
        # read_data_result = OM_entry.SS_read_data()
        # logger.debug(f"SS_read_data result: {read_data_result}")

        # DevID_rd_res = OM_entry.Get_DevID()
        # logger.debug(f"Current DevID result: {DevID_rd_res}")
      
        # set_DevID_result = OM_entry.Set_DevID(2)
        # logger.debug(f"OM_set_DevID result: {set_DevID_result}")
        
        # DevID_rd_res = OM_entry.Get_DevID()
        # logger.debug(f"Current DevID result: {DevID_rd_res}")

        # take_data_result = OM_entry.SS_take_data()
        # logger.debug(f"SS_take_data result: {take_data_result}")
        # read_data_result = OM_entry.SS_read_data()
        # logger.debug(f"SS_read_data result: {read_data_result}")
# ---
# Flash sector readout example
        # flash_frag = []
        # for i in range(0, 64, 8):
        #     Flash_resp = OM_entry.CANWrp_ReadFlashFrag(i)
        #     if "data" in Flash_resp:
        #         flash_frag.extend(Flash_resp["data"])
        #     else:
        #         logger.error(f"Err occured at {i}: {Flash_resp}")
        #         break

        # # flash_frag contains bytes. Print them as 32-bit hexes with 0 at the beginning if needed
        # for i in range(0, len(flash_frag), 4):
        #     val = (int.from_bytes(flash_frag[i]) << 24) | (int.from_bytes(flash_frag[i+1]) << 16) | (int.from_bytes(flash_frag[i+2]) << 8) | int.from_bytes(flash_frag[i+3])
        #     print(f"{val:08X}")


        # take_data_result = OM_entry.SS_take_data()
        # logger.debug(f"SS_take_data result: {take_data_result}")
        # read_data_result = OM_entry.SS_read_data()
        # logger.debug(f"SS_read_data result: {read_data_result}")

# ---
#       
        # OM_entry._Cmd_SetMnfID()

        # CB_resp = OM_entry.CANWrp_ReadCB()
        # logger.info(f"Current CB: {CB_resp}")

        resp = OM_entry.Data_GetNonCanCurrBlock()
        logger.info(resp)

        resp = OM_entry.Data_GetFWVer()
        logger.info(resp)

        resp = OM_entry.Data_GetMnfID()
        logger.info(resp)


    except Exception as e:
        print(e)

    modbus_worker.stop()
