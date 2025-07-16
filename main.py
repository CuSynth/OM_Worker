from OM_worker_base import OM_Interface
from modbus_worker import ModbusWorker
from MB_over_CAN_worker import MBOverCANWorker
from usb_can_driver.usb_can import USB_CAN_Driver
from loguru import logger
import matplotlib.pyplot as plt
import time
import numpy as np
from PIL import Image
import cv2 

# ResetSrc
SLAVE_ADDR  = 2
COMM_PORT   = "COM9"
BAUDRATE    = 500000


path_to_work = 'OM_GRI_log/Gri04/'

def main():
    logger.add(path_to_work + "logging.log", level="DEBUG", rotation="5 MB", retention="4 week")
    logger.info("Application started")

    try:
        if True:
            interace_worker = ModbusWorker (
                    port=COMM_PORT, baudrate=BAUDRATE, stopbits=1, parity="N", bytesize=8
            )
        else:
            can_driver = USB_CAN_Driver()
            can_driver.connect(COMM_PORT)
            interace_worker = MBOverCANWorker(can_driver, dev_id=4, port_to_use=0)


        OM_entry = OM_Interface(interace_worker, slave_id=SLAVE_ADDR)    
        interace_worker.start()
        time.sleep(0.1)
        logger.info("Modbus worker started")

        GRI_tst(OM_entry=OM_entry)
        # Example_GetSSData(OM_entry)
        # Playground(OM_entry)
        # res = OM_entry.Data_ReadTemperature()
        # logger.info(f"Temperature: {res}")

    except Exception as e:
        print(e)

    interace_worker.stop()
    plt.show()


def Playground(OM_entry: OM_Interface):
    # Example_GetSetDevID(OM_entry, ID=4)
    # return
    # Example_UploadFW(OM_entry)
    # Example_FixValid(OM_entry)
    # Example_CheckCRC(OM_entry)
    # Example_SetPref(OM_entry)
    # Example_GetFW_ID(OM_entry)

    # return

    # OM_entry.slave_id = 2
    # Example_GetGAM(OM_entry=OM_entry)


    res = OM_entry.Cmd_SSTake()
    res = OM_entry.Cmd_HSTake()
    res = OM_entry.Cmd_GAMTake()

    time.sleep(0.5)

    Example_Read_Grayscale_Photo(OM_entry=OM_entry, photo_take=False, save_path='SS_photo/SunPhoto.png')
    Example_Read_Thermal_Photo(OM_entry=OM_entry, photo_take=False, save_path="SS_photo/ThtmlPhoto.png")
    res = OM_entry.Data_GetGAM()

    # ret = OM_entry.Data_GetSSMtxSet()
    # logger.info(f"SS_MTX_Set: {ret}")
    # Example_GetFW_ID(OM_entry)



def GRI_tst(OM_entry: OM_Interface):
    OM_ID = '10130'
    OM_entry.slave_id = 0x06

    FWID_rd_res = OM_entry.Data_GetFW_ID()
    logger.info(f"FW_ID: {FWID_rd_res}")

    ret = OM_entry.Data_GetDevID()
    logger.info(f"DevID: {ret}")

    ret = OM_entry.Data_GetMnfID()
    logger.info(f"MnfID: {ret}")

    Example_CheckCRC(OM_entry)

    Example_GetGAM(OM_entry)

    Example_Read_Grayscale_Photo(OM_entry=OM_entry, save_path=path_to_work+'/Photo/SS_'+OM_ID+'.png', photo_take=True)

    Example_Read_Thermal_Photo(OM_entry=OM_entry, save_path=path_to_work+'/Photo/HS_'+OM_ID+'.png', photo_take=True)

    ret = OM_entry.Data_GetSSMtxSet()
    logger.info(f"SS_MTX_Set: {ret}")

    ret = OM_entry.Data_GetSSAlgoSet()
    logger.info(f"SS_Algo_Set: {ret}")

    return



def Example_Read_Grayscale_Photo(OM_entry: OM_Interface, save_path='OM_img.png', photo_take=False):
    if photo_take:
        OM_entry.Cmd_SSTake()
        time.sleep(0.2)
        res = OM_entry.Data_GetSS()
        logger.info(f"SS_read_data result: {res}")
        res = OM_entry.Data_GetCmdStatus()
        logger.info(f"SS_cmd_status result: {res}")

    time.sleep(0.3)
    # Read the full 480x480 grayscale image
    result = OM_entry.Read_SS_Grayscale_Photo()
    if "error" in result:
        logger.info(f"Error reading grayscale photo: {result['error']}")
    else:
        logger.info(f"Grayscale photo read successfully. Raw bytes length: {len(result['raw'])}")
        # Normalize to 8-bit for PNG saving
        image = np.array(result["data"])
        img8 = (image / image.max() * 255).astype(np.uint8)
        img_pil = Image.fromarray(img8, mode="L")
        img_pil.save(save_path)

        # color_img = cv2.cvtColor(img8, cv2.COLOR_BAYER_BG2RGB)
        # plt.figure()
        # plt.imshow(color_img)
        # plt.title("SunSens Bayer Color Image")
        # plt.show(block=False)
        # plt.pause(0.001)

        plt.figure()
        plt.imshow(image, cmap="gray")
        plt.title("SunSens Image")
        plt.show(block=False)
        plt.pause(0.001)

def Example_Read_Grayscale_Lines(OM_entry: OM_Interface, start_line: int, end_line: int):
    # Read lines N..M (e.g., lines 10 to 20)
    result = OM_entry.Read_SS_Grayscale_Lines(start_line, end_line)
    if "error" in result:
        print(f"Error reading grayscale lines: {result['error']}")
    else:
        print(f"Grayscale lines {start_line}-{end_line} read successfully. Raw bytes length: {len(result['raw'])}")

        # plot lines with imshow
        plt.figure()
        plt.imshow(result["data"], cmap='gray')
        plt.title("SunSens Image by lines")
        plt.show(block=False)
        plt.pause(0.001)


def Example_Read_Thermal_Photo(OM_entry: OM_Interface, save_path=None, photo_take=False):
    if photo_take:
        OM_entry.Cmd_HSTake()
        time.sleep(0.3)

    # Read the full 32x24 thermal image
    result = OM_entry.Read_Thermal_Photo()
    if "error" in result:
        print(f"Error reading thermal photo: {result['error']}")
    else:
        print(f"Thermal photo read successfully. Raw bytes length: {len(result['raw'])}")

        image = np.array(result['data'])
        plt.figure()
        plt.imshow(image, cmap="inferno")
        plt.colorbar(label="Temperature")
        plt.title("Thermal Image")
        plt.show(block=False)
        plt.pause(0.001)

        if save_path:
            img8 = (image / image.max() * 255).astype(np.uint8)
            img_pil = Image.fromarray(img8, mode="L")
            img_pil.save(save_path)



def Example_GetGAM(OM_entry: OM_Interface):
    ret = OM_entry.Cmd_GAMTake()
    # logger.info(f"GAM cmd sent: {ret}")

    ret = OM_entry.Data_GetGAM()
    logger.info(f"GAM: {ret}")

def Example_GetSSData(OM_entry: OM_Interface):
    for i in range(1):
        logger.info(f"Iteration {i+1}")
        res = OM_entry.Cmd_SSTake()
        logger.info(f"SS_take_data result: {res}")
        time.sleep(0.2)
 
        res = OM_entry.Data_GetSS()
        logger.info(f"SS_read_data result: {res}")
        time.sleep(0.1)

        res = OM_entry.Data_GetCmdStatus()
        logger.info(f"SS_cmd_status result: {res}")


def Example_GetSetDevID(OM_entry: OM_Interface, ID: int = 1):
    DevID_rd_res = OM_entry.Data_GetDevID()
    logger.info(f"Current DevID result: {DevID_rd_res}")
    
    set_DevID_result = OM_entry.Cmd_SetDevID(ID)
    logger.info(f"OM_set_DevID result: {set_DevID_result}")
    
    DevID_rd_res = OM_entry.Data_GetDevID()
    logger.info(f"Current DevID result: {DevID_rd_res}")

    OM_entry.Cmd_ForceReboot()
    time.sleep(0.2)


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
    logger.info(f"Current ControlBlock: {CB_resp}")

    resp = OM_entry.Blt_CheckImgValid(0)
    logger.info(f"Check CRC_0 res: {resp}")

    resp = OM_entry.Blt_CheckImgValid(1)
    logger.info(f"Check CRC_1 res: {resp}")


def Example_CheckCRC(OM_entry: OM_Interface):
    Example_CheckValid(OM_entry)

    img_0_file = 'OM_GRI_log/OMMCU_v03_00_01_m.bin'
    logger.info(f"Checking CRC for img_0: {img_0_file}")
    resp = OM_entry.Blt_CheckCRC(0, file_path=img_0_file)
    logger.info(f"Check valid of img_0 res: {resp}")

    # resp = OM_entry.Blt_CheckCRC(1, file_path='FWs/OMMCU_v02_10_21_r.bin')
    # logger.info(f"Check valid of img_1 res: {resp}")



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
    logger.info(f"Check CRC_2 res: {resp}")
    
    # resp = OM_entry.Blt_FixValid(1)
    # logger.info(f"Fix CRC_1 res: {resp}")

    # resp = OM_entry.Blt_CheckImgValid(1)
    # logger.info(f"Check CRC_1 res: {resp}")


def Example_Reboot(OM_entry: OM_Interface):
    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")
    
    resp = OM_entry.Blt_Restart()
    logger.info(f"Restart resp: {resp}")

    time.sleep(0.1)

    CB_resp = OM_entry.CANWrp_ReadCB()
    logger.info(f"Current CB: {CB_resp}")

def Example_SetPref(OM_entry: OM_Interface):
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

    # return

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


def Example_UploadFW(OM_entry: OM_Interface):
    logger.info("Starting firmware upload example...")
    logger.info(f"Getting FW_ID and checking validity...")
    Example_GetFW_ID(OM_entry)
    Example_CheckValid(OM_entry)

    logger.info("Setting pref FW to 0...")
    ret = OM_entry.Blt_SetPref(pref=0)
    logger.info(f"Set_pref ret: {ret}")

    logger.info("Restarting the device... (may not return any value)")
    resp = OM_entry.Blt_Restart()
    logger.info(f"Restart resp: {resp}")

    time.sleep(1)

    logger.info("Erasing second half of flash memory...")
    Example_EraseHalf(OM_entry)

    time.sleep(5)

    logger.info("Getting FW_ID and checking validity after erase...")
    Example_GetFW_ID(OM_entry)
    Example_CheckValid(OM_entry)

    logger.info("Uploading firmware...")
    ret = OM_entry.Blt_UploadFW(image=1, file='FWs/OMMCU_v02_10_21_r.bin')
    logger.info(f"FW_upload ret: {ret}")

    logger.info("Checking validity after upload...")
    Example_CheckValid(OM_entry)
    OM_entry.Blt_Restart()

    time.sleep(1)

    logger.info("Checking validity after restart...")
    Example_CheckValid(OM_entry)
    Example_GetFW_ID(OM_entry)

    logger.info("Setting pref to 1 and rebooting...")
    ret = OM_entry.Blt_SetPref(pref=1)
    logger.info(f"Set_pref ret: {ret}")
    Example_Reboot(OM_entry)


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


# Example Usagepymodbus
if __name__ == "__main__":
    main()

