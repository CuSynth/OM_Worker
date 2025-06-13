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
from main import *

# For plain RS-485 communication
COMM_PORT   = "COM9"
BAUDRATE    = 500000

# Path to log and save photos
path_to_work = 'log/'

# OM under test address
SLAVE_ADDR  = 2

FW_to_upload = 'FWs/OMMCU_v03_01_00_r.bin'  # Path to the firmware file to upload

# План на проверку:
# 1. Проверка связи с ДСГ: GRI_tst (читатет измерения и фото)
# 2. Обновить ПО во второй половине памяти: GRI_upload_2pt_FW:
#  - Перейти в основную область и стереть вторую половину памяти
#  - Загрузить новое ПО во вторую половину памяти
#  - Выставить вторую половину памяти как предпочтительную и перезагрузить устройство
#  - Проверить, что после перезагрузки устройство работает с новым ПО 
#  (В логах будет результат чтения версии нового ПО)
# 4. Выставить первую область памяти как предпочтительную и перезагрузить устройство

def main():
    logger.add(path_to_work + "logging.log", level="DEBUG", rotation="5 MB", retention="4 week")
    logger.info("Application started")

    
    try:
        if False: # Change to True if using RS-485
            interace_worker = ModbusWorker (
                    port=COMM_PORT, baudrate=BAUDRATE, stopbits=1, parity="N", bytesize=8
            )
        else:
            can_driver = USB_CAN_Driver()
            can_driver.connect('COM5')
            interace_worker = MBOverCANWorker(can_driver, dev_id=4, port_to_use=0)


        OM_entry = OM_Interface(interace_worker, slave_id=SLAVE_ADDR)    
        interace_worker.start()
        time.sleep(0.1)
        logger.info("Modbus worker started")


        GRI_tst(OM_entry)
        GRI_upload_2pt_FW(OM_entry) # Закомментировать, если не нужно обновлять ПО
        

    except Exception as e:
        print(e)

    interace_worker.stop()
    plt.show()


def Test_Communication(OM_entry: OM_Interface):
    logger.info("Testing communication with OM...")
    
    Example_GetSSData(OM_entry)
    Example_GetGAM(OM_entry)
    
    logger.info("Testing communication with OM finished")


def GRI_tst(OM_entry: OM_Interface):
    logger.info("Getting measurements...")
    Test_Communication(OM_entry)


    logger.info("Read and save photos...")
    Example_Read_Grayscale_Photo(OM_entry=OM_entry, photo_take=True, save_path=path_to_work+'Photo/Sun.png')
    Example_Read_Thermal_Photo(OM_entry=OM_entry, save_path=path_to_work+'Photo/horizon.png')

    logger.info("Getting SS_MTX_Set...")
    ret = OM_entry.Data_GetSSMtxSet()
    logger.info(f"SS_MTX_Set: {ret}")
    
    logger.info("Getting FW_ID...")
    Example_GetFW_ID(OM_entry)

def GRI_upload_2pt_FW(OM_entry: OM_Interface):
    # Читаем текущее состояние датчика
    logger.info("Starting firmware upload example...")
    logger.info(f"Getting FW_ID and checking validity...")
    Example_GetFW_ID(OM_entry)
    Example_CheckValid(OM_entry)    # Проверяет текущую структуру-описатель памяти и проверяет обе CRC.

    # Переходим в основную область памяти
    logger.info("Setting pref FW to 0...")
    ret = OM_entry.Blt_SetPref(pref=0)
    logger.info(f"Set_pref ret: {ret}")

    logger.info("Restarting the device... (may not return any value)")
    resp = OM_entry.Blt_Restart()
    logger.info(f"Restart resp: {resp}")

    time.sleep(1)

    # Стираем вторую половину памяти
    logger.info("Erasing second half of flash memory...")
    Example_EraseHalf(OM_entry)

    time.sleep(5)

    # Проверяем, что вторая половина памяти стерта
    logger.info("Getting FW_ID and checking validity after erase...")
    Example_GetFW_ID(OM_entry)
    Example_CheckValid(OM_entry)

    # Загружаем новое ПО во вторую половину памяти
    logger.info("Uploading firmware...")
    ret = OM_entry.Blt_UploadFW(image=1, file=FW_to_upload)
    logger.info(f"FW_upload ret: {ret}")

    # Проверяем, что ПО загружено
    logger.info("Checking validity after upload...")
    Example_CheckValid(OM_entry)
    OM_entry.Blt_Restart()

    time.sleep(3)

    # Проверяем утройство после перезагрузки: 
    #   Если первая половина не была подрисана - мы запустимся во второй. 
    #   Если была - останемся в первой и обе будут валидны
    logger.info("Checking validity after restart...")
    Example_CheckValid(OM_entry)
    Example_GetFW_ID(OM_entry)

    # Выставляем вторую половину памяти как предпочтительную и перезагружаем устройство
    logger.info("Setting pref to 1 and rebooting...")
    ret = OM_entry.Blt_SetPref(pref=1)
    logger.info(f"Set_pref ret: {ret}")
    Example_Reboot(OM_entry)

    time.sleep(5)

    # Проверяем, что устройство работает с новым ПО
    logger.info("Checking FW_ID after reboot...")
    Example_GetFW_ID(OM_entry)

    # Возвращаемся к первой половине памяти
    logger.info("Setting pref to 1 and rebooting...")
    ret = OM_entry.Blt_SetPref(pref=0)
    logger.info(f"Set_pref ret: {ret}")
    Example_Reboot(OM_entry)

    time.sleep(5)
    Example_GetFW_ID(OM_entry)
    Example_CheckValid(OM_entry)


if __name__ == "__main__":
    main()

