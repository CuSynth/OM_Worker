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

# UART (modbus) setup
COM_PORT   = "COM9"
COM_BAUD    = 500000

# CAN bus port
CAN_COM_PORT = "COM4"

log_name = 'logging.log'
test_log_path = 'logs/Test_logs/'
mnf_log_path = 'logs/Mnf_logs/'

def main():
    # OM_mnf_ReleaseProcess()
    OM_mnf_TestProcess()


def OM_mnf_ReleaseProcess():
    try:
        slaveID = 0x01
        mnfID = 0x00010100
        MnfID_undertest = f'{mnfID:05x}'

        # Prepare newly manufactured OM:
        worker, OM_entry = OM_comm_ini(log_Path=mnf_log_path, log_name=log_name, UseCANBUS=False, slave_ID=slaveID)
        
        # Force set new ID
        OM_mnf_ForceSetID(OM_entry=OM_entry, ID=slaveID)    
        # Update MnfID
        OM_mnf_ForceSetMnfID(OM_entry=OM_entry, ID=mnfID)
        # Test OM
        OM_periph_tst(OM_entry=OM_entry, path_to_work=test_log_path, MnfID_undertest=MnfID_undertest)

    except Exception as e:
        print(e)

    worker.stop()
    plt.show()

def OM_mnf_TestProcess():
    try:
        slaveID = 0x01
        mnfID = 0x00010100
        MnfID_undertest = f'{mnfID:05x}'

        # Test any OM
        worker, OM_entry = OM_comm_ini(log_Path=test_log_path, log_name=log_name, UseCANBUS=False, slave_ID=slaveID)
        OM_periph_tst(OM_entry=OM_entry, path_to_work=test_log_path, MnfID_undertest=MnfID_undertest)

    except Exception as e:
        print(e)

    worker.stop()
    plt.show()


def OM_mnf_ForceSetID(OM_entry: OM_Interface, ID: int):
    OM_entry.slave_id = 0x00
    OM_entry.Cmd_SetDevID(ID=ID)
    time.sleep(3)

    OM_entry.Cmd_ForceReboot()
    OM_entry.slave_id = ID
    time.sleep(0.2)


def OM_mnf_ForceSetMnfID(OM_entry: OM_Interface, ID: int):
    OM_entry._Cmd_SetMnfID(ID=ID)
    time.sleep(3)


def OM_periph_tst(OM_entry: OM_Interface, path_to_work:str, MnfID_undertest:str):
    FWID_rd_res = OM_entry.Data_GetFW_ID()
    logger.info(f"FW_ID: {FWID_rd_res}")

    ret = OM_entry.Data_GetDevID()
    logger.info(f"DevID: {ret}")

    ret = OM_entry.Data_GetMnfID()
    logger.info(f"MnfID: {ret}")

    Example_CheckCRC(OM_entry)

    Example_GetGAM(OM_entry)

    Example_Read_Grayscale_Photo(OM_entry=OM_entry, save_path=path_to_work+'/Photo/SS_'+MnfID_undertest+'.png', photo_take=True)

    Example_Read_Thermal_Photo(OM_entry=OM_entry, save_path=path_to_work+'/Photo/HS_'+MnfID_undertest+'.png', photo_take=True)

    ret = OM_entry.Data_GetSSMtxSet()
    logger.info(f"SS_MTX_Set: {ret}")

    ret = OM_entry.Data_GetSSAlgoSet()
    logger.info(f"SS_Algo_Set: {ret}")

    return


def OM_comm_ini(log_Path: str, log_name: str, UseCANBUS: bool, slave_ID: int):
    logger.add(log_Path + log_name, level="DEBUG", rotation="5 MB", retention="4 week")
    logger.info("Application started")

    if not UseCANBUS:
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

    return interace_worker, OM_entry


if __name__ == "__main__":
    main()
