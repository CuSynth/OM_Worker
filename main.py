from OM_worker_base import *
from loguru import logger
from blt_logic import analyze_bin_file


SLAVE_ADDR  = 2
COMM_PORT   = "COM9"
BAUDRATE    = 500000

def Playground(OM_entry: OM_Interface):
    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")

    resp = OM_entry.Blt_CheckImgValid(0)
    logger.info(f"Check CRC_0 res: {resp}")

    resp = OM_entry.Blt_CheckImgValid(1)
    logger.info(f"Check CRC_1 res: {resp}")



def main():
    logger.add("logs/app.log", level="DEBUG", rotation="500 KB", retention="1 week")
    logger.info("Application started")
    modbus_worker: ModbusWorker = ModbusWorker (
            port=COMM_PORT, baudrate=BAUDRATE, stopbits=1, parity="N", bytesize=8
        )
    try:
        OM_entry = OM_Interface(modbus_worker, slave_id=SLAVE_ADDR)    
        modbus_worker.start()
        time.sleep(0.1)
        logger.info("Modbus worker started")


        Example_GetSSData(OM_entry)
        Playground(OM_entry)
        Example_GetSSData(OM_entry)

    except Exception as e:
        print(e)

    modbus_worker.stop()





def Example_GetSSData(OM_entry: OM_Interface):
    for i in range(1):
        logger.info(f"Iteration {i+1}")
        res = OM_entry.Cmd_SSTake()
        logger.info(f"SS_take_data result: {res}")

        res = OM_entry.Data_GetSS()
        logger.info(f"SS_read_data result: {res}")
        time.sleep(0.1)

def Example_GetSetDevID(OM_entry: OM_Interface):
    Example_GetSSData(OM_entry)

    DevID_rd_res = OM_entry.Data_GetDevID()
    logger.debug(f"Current DevID result: {DevID_rd_res}")
    
    set_DevID_result = OM_entry.Cmd_SetDevID(2)
    logger.debug(f"OM_set_DevID result: {set_DevID_result}")
    
    DevID_rd_res = OM_entry.Data_GetDevID()
    logger.debug(f"Current DevID result: {DevID_rd_res}")

    Example_GetSSData(OM_entry)

def Example_FLASHSectRd(OM_entry: OM_Interface):
    flash_frag = []
    for i in range(0, 64, 8):
        Flash_resp = OM_entry.CANWrp_ReadFlashFrag(i)
        if "data" in Flash_resp:
            flash_frag.extend(Flash_resp["data"])
        else:
            logger.error(f"Err occured at {i}: {Flash_resp}")
            break

    # flash_frag contains bytes. Print them as 32-bit hexes with 0 at the beginning if needed
    for i in range(0, len(flash_frag), 4):
        val = (int.from_bytes(flash_frag[i]) << 24) | (int.from_bytes(flash_frag[i+1]) << 16) | (int.from_bytes(flash_frag[i+2]) << 8) | int.from_bytes(flash_frag[i+3])
        print(f"{val:08X}")

    Example_GetSSData(OM_entry)


def Example_SysCmd(OM_entry: OM_Interface):
    # OM_entry._Cmd_SetMnfID()

    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")

    resp = OM_entry.Data_GetNonCanCurrBlock()
    logger.info(resp)

    resp = OM_entry.Data_GetFWVer()
    logger.info(resp)

    resp = OM_entry.Data_GetMnfID()
    logger.info(resp)

# Example Usagepymodbus
if __name__ == "__main__":
    main()

