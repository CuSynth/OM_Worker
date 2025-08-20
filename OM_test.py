from OM_worker_base import OM_Interface
from modbus_worker import ModbusWorker
from MB_over_CAN_worker import MBOverCANWorker
from usb_can_driver.usb_can import USB_CAN_Driver
from loguru import logger
import matplotlib.pyplot as plt
import time
import os
from main import *


# UART (modbus) setup
COM_PORT   = "COM7"
COM_BAUD    = 500000

# CAN bus port
# CAN_COM_PORT = "COM4"

log_name = 'logging.log'
test_log_path = 'Testing_logs/'
test_photos_path = 'Testing_logs/Photos/'

def OM_TestProcess():
    if not os.path.exists(test_photos_path):
        os.makedirs(test_photos_path)

    logger.add(test_log_path + log_name, level="DEBUG", rotation="5 MB", retention="4 week")
    logger.info("Application started")
    interace_worker = None

    try:
        # Установка ID для опроса
        slave_ID = 0x01

        # True для использования Rs-485
        if True:
            interace_worker = ModbusWorker (
                    port=COM_PORT, baudrate=COM_BAUD, stopbits=1, parity="N", bytesize=8
            )
        else:
            can_driver = USB_CAN_Driver()
            can_driver.connect(CAN_COM_PORT)
            interace_worker = MBOverCANWorker(can_driver, dev_id=4, port_to_use=0)

        OM_entry = OM_Interface(interace_worker, slave_id=slave_ID)
        interace_worker.start()
        time.sleep(0.1)
        logger.info("Modbus worker started")

        OM_periph_tst(OM_entry=OM_entry)

    except Exception as e:
        print(e)

    logger.info("Modbus worker finished")

    plt.show()
    logger.remove()
    if interace_worker:
        interace_worker.stop()


def OM_periph_tst(OM_entry: OM_Interface):
    # Чтение версии ПО ДСГ
    FWID_rd_res = OM_entry.Data_GetFW_ID()
    logger.info(f"FW_ID: {FWID_rd_res}")

    # Чтение адреса ДСГ
    ret = OM_entry.Data_GetDevID()
    logger.info(f"DevID: {ret}")

    # Чтение производственного номера ДСГ
    ret = OM_entry.Data_GetMnfID()
    logger.info(f"MnfID: {ret}")


    # ===================
    # Измерение и чтение данных ДУС/Акселя/Магнитометра
    Example_GetGAM(OM_entry)

    # Чтение температуры
    res = OM_entry.Data_ReadTemperature()
    logger.info(f"Temperature: {res["data"]}")

    # ===================
    # Измерение и чтение результата ДС
    Example_GetSSData(OM_entry)

    # Чтение ЧБ фото
    Example_Read_Grayscale_Photo(OM_entry=OM_entry, save_path=test_photos_path+'SS_image.png', photo_take=False)
    
    # ===================
    # # Установка настроек алгоритма кластеризации (определение горячего на фом=не комнаты)
    # ret = OM_entry.Set_Cluster_Bound_Value(100, 30, 5)
    # logger.info(f"Setting clust bound result: {ret}")

    # Измерение ДГ
    OM_entry.Cmd_HSTake()

    # Чтение теплового снимка
    Example_Read_Thermal_Photo(OM_entry=OM_entry, save_path=test_photos_path+'HS_image.png', photo_take=False)

    # Чтение кластеризованного снимка
    Example_Read_Thermal_Cluster(OM_entry=OM_entry, photo_take=False)

    # ===================
    # Чтение настроек матрицы ДС
    ret = OM_entry.Data_GetSSMtxSet()
    logger.info(f"SS_MTX_Set: {ret}")

    # Чтение калибровок
    ret = OM_entry.Data_GetSSAlgoSet()
    logger.info(f"SS_Algo_Set: {ret}")

    return



def main():
    OM_TestProcess()

if __name__ == "__main__":
    main()
