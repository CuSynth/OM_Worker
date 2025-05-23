from OM_worker_base import *
from loguru import logger
from blt_logic import analyze_bin_file

# ResetSrc
SLAVE_ADDR  = 2
COMM_PORT   = "COM9"
BAUDRATE    = 500000

def Playground(OM_entry: OM_Interface):
    Example_UploadFWAndCopyAndGo(OM_entry=OM_entry)



def main():
    logger.add("logs/OM_wrkr.log", level="DEBUG", rotation="5 MB", retention="4 week")
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



def Example_UploadFW(OM_entry: OM_Interface):
    Example_GetFW_ID(OM_entry)
    Example_CheckValid(OM_entry)


    ret = OM_entry.Blt_SetPref(pref=0)
    logger.info(f"FW_upload ret: {ret}")

    resp = OM_entry.Blt_Restart()
    logger.info(f"Restart resp: {resp}")

    time.sleep(1)

    Example_EraseHalf(OM_entry)

    time.sleep(5)

    Example_GetFW_ID(OM_entry)
    Example_CheckValid(OM_entry)


    ret = OM_entry.Blt_UploadFW(image=1, file='FWs/OMMCU_v02_10_01_r.bin')
    logger.info(f"FW_upload ret: {ret}")

    Example_CheckValid(OM_entry)
    OM_entry.Blt_Restart()

    time.sleep(1)

    Example_CheckValid(OM_entry)
    Example_GetFW_ID(OM_entry)

def Example_UploadFWAndCopyAndGo(OM_entry: OM_Interface):
    Example_GetFW_ID(OM_entry)
    Example_CheckValid(OM_entry)

    ret = OM_entry.Blt_SetPref(pref=0)
    logger.info(f"FW_upload ret: {ret}")

    resp = OM_entry.Blt_Restart()
    logger.info(f"Restart resp: {resp}")

    time.sleep(1)

    Example_EraseHalf(OM_entry)

    time.sleep(5)

    Example_GetFW_ID(OM_entry)
    Example_CheckValid(OM_entry)

    ret = OM_entry.Blt_UploadFW(image=1, file='FWs/OMMCU_v02_10_07_m.bin')
    logger.info(f"FW_upload ret: {ret}")

    Example_CheckValid(OM_entry)

    resp = OM_entry.Blt_CopyAndGo(file_path='FWs/OMMCU_v02_10_07_m.bin')
    logger.info(f"Copy and go res: {resp}")
    
    time.sleep(1)

    Example_CheckValid(OM_entry)
    Example_GetFW_ID(OM_entry)




def Example_GetSSData(OM_entry: OM_Interface):
    for i in range(1):
        logger.info(f"Iteration {i+1}")
        res = OM_entry.Cmd_SSTake()
        logger.info(f"SS_take_data result: {res}")

        res = OM_entry.Data_GetSS()
        logger.info(f"SS_read_data result: {res}")
        time.sleep(0.1)

def Example_GetSetDevID(OM_entry: OM_Interface):
    DevID_rd_res = OM_entry.Data_GetDevID()
    logger.debug(f"Current DevID result: {DevID_rd_res}")
    
    set_DevID_result = OM_entry.Cmd_SetDevID(2)
    logger.debug(f"OM_set_DevID result: {set_DevID_result}")
    
    DevID_rd_res = OM_entry.Data_GetDevID()
    logger.debug(f"Current DevID result: {DevID_rd_res}")


def Example_GetFW_ID(OM_entry: OM_Interface):
    FWID_rd_res = OM_entry.Data_GetFW_ID()
    logger.info(f"Current DFW_ID result: {FWID_rd_res}")

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


def Example_CheckValid(OM_entry: OM_Interface):
    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")

    resp = OM_entry.Blt_CheckImgValid(0)
    logger.info(f"Check CRC_0 res: {resp}")

    resp = OM_entry.Blt_CheckImgValid(1)
    logger.info(f"Check CRC_1 res: {resp}")


def Example_CheckCRC(OM_entry: OM_Interface):
    Example_CheckValid(OM_entry)

    resp = OM_entry.Blt_CheckCRC(0, file_path='FWs/OMMCU_v02_09_09_m.bin')
    logger.info(f"Check valid of img_0 res: {resp}")

    resp = OM_entry.Blt_CheckCRC(1, file_path='FWs/OMMCU_v02_09_09_r.bin')
    logger.info(f"Check valid of img_1 res: {resp}")



def Example_EraseBySector(OM_entry: OM_Interface):
    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")
    
    resp = OM_entry.Blt_EraseSector(5)
    logger.info(f"Check CRC_1 res: {resp}")

    resp = OM_entry.Blt_EraseSector(6)
    logger.info(f"Check CRC_1 res: {resp}")

    resp = OM_entry.Blt_EraseSector(7)
    logger.info(f"Check CRC_1 res: {resp}")


def Example_EraseHalf(OM_entry: OM_Interface):
    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")
    
    resp = OM_entry.Blt_EraseHalf()
    logger.info(f"Erase second half res: {resp}")



def Example_FixValid(OM_entry: OM_Interface):
    resp = OM_entry.Blt_CheckImgValid(0)
    logger.info(f"Check CRC_1 res: {resp}")
    
    resp = OM_entry.Blt_FixValid(0)
    logger.info(f"Fix CRC_1 res: {resp}")

    resp = OM_entry.Blt_CheckImgValid(0)
    logger.info(f"Check CRC_1 res: {resp}")


    resp = OM_entry.Blt_CheckImgValid(1)
    logger.info(f"Check CRC_1 res: {resp}")
    
    resp = OM_entry.Blt_FixValid(1)
    logger.info(f"Fix CRC_1 res: {resp}")

    resp = OM_entry.Blt_CheckImgValid(1)
    logger.info(f"Check CRC_1 res: {resp}")


def Example_Reboot(OM_entry: OM_Interface):
    Example_CheckValid(OM_entry=OM_entry)

    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")
    resp = OM_entry.Blt_SetPref(1)
    logger.info(f"Set pref: {resp}")
    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")

    resp = OM_entry.Blt_Restart()
    logger.info(f"Restart resp: {resp}")

    time.sleep(2)

    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")
    resp = OM_entry.Blt_SetPref(0)
    logger.info(f"Set pref: {resp}")
    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")

    resp = OM_entry.Blt_Restart()
    logger.info(f"Restart resp: {resp}")
    
    time.sleep(2)
    
    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")



def Example_CopyAndGo(OM_entry: OM_Interface):
    Example_CheckValid(OM_entry=OM_entry)
    Example_GetFW_ID(OM_entry)

    resp = OM_entry.Blt_CheckCRC(1, file_path='FWs/OMMCU_v02_09_12_m.bin')
    logger.info(f"Check valid of MainFW in img_1 res: {resp}")

    resp = OM_entry.Blt_CopyAndGo(file_path='FWs/OMMCU_v02_09_12_m.bin')
    logger.info(f"Copy and go res: {resp}")

    time.sleep(1)

    Example_CheckValid(OM_entry=OM_entry)
    Example_GetFW_ID(OM_entry)




# Example Usagepymodbus
if __name__ == "__main__":
    main()

