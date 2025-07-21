import time
import struct
from loguru import logger
from OM_registers import *
from OM_data import *
from blt_logic import *
from PIL import Image
import numpy as np
from tqdm import tqdm  # Add this import at the top of your file
from OM_comm_interface import *
from modbus_worker import *

class OM_Interface:
    def __init__(self, comm_worker, slave_id=1):
        self.modbus_worker = comm_worker
        self.slave_id = slave_id
        logger.info(f"Initialized OM Interface with slave ID: {slave_id}")

    def _build_command(self, request_type, address, count=0, registers:list = [], reversed_registers:bool=True):
        if request_type == ModbusRequestType.WRITE_MULTY:
            if reversed_registers:
                registers = [(((reg & 0x00FF) << 8) | ((reg >> 8) & 0x00FF)) for reg in registers]
            return ModbusRequest(
                type=ModbusRequestType.WRITE_MULTY, address=address, registers=registers, slave_id=self.slave_id
            )
        elif request_type == ModbusRequestType.READ:
            return ModbusRequest(
                type=ModbusRequestType.READ, address=address, count=count, slave_id=self.slave_id
            )
        else:
            logger.error(f"Unknown request type: {request_type}")
            raise ValueError("Unknown request type")

    def send_modbus(self, command, blocking=True, timeout=5, silent=False):
        return self.modbus_worker.send_request(command, blocking=blocking, timeout=timeout, silent=silent)

    def Cmd_ForceReboot(self):
        pack = OM_BuildCmd_Reboot()
        registers = PackToRegisters(pack)
        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_CMD_REG_ADDR+OM_CMD_OFF, registers=registers)
        logger.debug(f"Sending reboot command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        return response

    def Cmd_SetDevID(self, ID : int):
        pack = OM_build_set_DevID(ID)
        registers = PackToRegisters(pack)
        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_CMD_REG_ADDR+OM_CMD_OFF, registers=registers)
        logger.debug(f"Sending SetDevID command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        return response

    def Cmd_SSTake(self):
        pack = OM_build_cmd_SS_take()
        registers = PackToRegisters(pack)
        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_CMD_REG_ADDR+OM_CMD_OFF, registers=registers)
        logger.debug(f"Sending SSTake command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        return response

    def Cmd_HSTake(self):
        pack = OM_build_cmd_HS_take()
        registers = PackToRegisters(pack)
        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_CMD_REG_ADDR+OM_CMD_OFF, registers=registers)
        logger.debug(f"Sending HSTake command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        return response


    def Cmd_GAMTake(self):
        pack = OM_build_cmd_GAM_take()
        registers = PackToRegisters(pack)
        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_CMD_REG_ADDR+OM_CMD_OFF, registers=registers)
        logger.debug(f"Sending SSTake command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        return response

    def _Cmd_SetMnfID(self, ID: int):
        pack = [0x1F, 0x00, 0x02, 0x00, ((ID >> 0) & 0xFF), ((ID >> 8) & 0xFF), ((ID >> 16) & 0xFF), ((ID >> 24) & 0xFF)]
        # pack = [0x1F, 0x00, 0x02, 0x00, 0x10, 0x00, 0x01, 0x00]
        registers = PackToRegisters(pack=pack)
        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_CMD_REG_ADDR+OM_CMD_OFF, registers=registers)
        logger.debug(f"Sending SSTake command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        return response


    def Data_GetFWVer(self):
        command = self._build_command(ModbusRequestType.READ, OM_CMD_REG_ADDR+OM_FW_VER_OFF, count=OM_FW_VER_LEN)
        response = self.modbus_worker.send_request(command, timeout=1)
        logger.debug(f"Getting FW version data: {command.__dict__}")
        
        if "data" in response:
            data = RegistersToPack(response["data"])
            response["data"] = {"FW version": OM_FWVer_parse(data)}
        return response

    def Data_GetMnfID(self):
        command = self._build_command(ModbusRequestType.READ, OM_CMD_REG_ADDR+OM_MNF_ID_OFF, count=OM_MNF_ID_LEN)
        response = self.modbus_worker.send_request(command, timeout=1)
        logger.debug(f"Getting  mnf ID data: {command.__dict__}")
        
        if "data" in response:
            data = RegistersToPack(response["data"])
            response["data"] = {"MnfID": OM_MnfID(data)}
        return response

    def Data_GetNonCanCurrBlock(self):
        command = self._build_command(ModbusRequestType.READ, OM_CMD_REG_ADDR+OM_CUR_REGION_OFF, count=OM_CUR_REGION_LEN)
        response = self.modbus_worker.send_request(command, timeout=1)
        logger.debug(f"Getting CurSect data: {command.__dict__}")
        
        if "data" in response:
            data = RegistersToPack(response["data"])
            response["data"] = {"Current sector": data[0]}
        return response


    def Data_GetSS(self, blocking=True, timeout=1):
        command = self._build_command(ModbusRequestType.READ, OM_SS_REG_ADDR+OM_SS_DATA_OFF, count=OM_SS_DATA_LEN)
        response = self.modbus_worker.send_request(command, blocking=blocking, timeout=timeout)
        logger.debug(f"Getting SS data: {command.__dict__}")
        if "data" in response:
            response["data"] = OM_SS_parse(response["data"])
        return response


    def Data_GetDevID(self, blocking=True, timeout=1):
        command = self._build_command(ModbusRequestType.READ, OM_CMD_REG_ADDR+OM_DEV_ID_OFF, count=OM_DEV_ID_LEN)
        response = self.modbus_worker.send_request(command, blocking=blocking, timeout=timeout)
        logger.debug(f"Sending SS_read_data: {command.__dict__}")
        if "data" in response:
            response["data"] = OM_parse_DevID(response["data"])
        return response

    def Data_GetFW_ID(self):
        command = self._build_command(ModbusRequestType.READ, OM_CMD_REG_ADDR+OM_FW_VER_OFF, count=OM_FW_VER_LEN)
        response = self.modbus_worker.send_request(command, blocking=True, timeout=1)
        logger.debug(f"Sending FW_read_data: {command.__dict__}")
        if "data" in response:
            response["data"] = OM_parse_FWVer(response["data"])
        return response        

    def Data_GetGAM(self):
        command = self._build_command(ModbusRequestType.READ, OM_GAM_REG_ADDR+OM_GAM_DATA_OFF, count=OM_GAM_DATA_LEN)
        response = self.modbus_worker.send_request(command, blocking=True, timeout=1)
        logger.debug(f"Getting GAM data: {command.__dict__}")
        if "data" in response:
            response["data"] = OM_GAM_parse(response["data"])
        return response

    def Data_GetSSMtxSet(self):
        command = self._build_command(ModbusRequestType.READ, OM_SS_REG_ADDR+OM_SS_MTX_SET_OFF, count=OM_SS_MTX_SET_LEN)
        response = self.modbus_worker.send_request(command, blocking=True, timeout=1)
        logger.debug(f"Getting SS matrix set data: {command.__dict__}")
        if "data" in response:
            response["data"] = OM_SS_parse_MtxSet(response["data"])
        return response

    def Data_GetCmdStatus(self):
        command = self._build_command(ModbusRequestType.READ, OM_CMD_REG_ADDR+OM_STATUS_OFF, count=OM_STATUS_LEN)
        response = self.modbus_worker.send_request(command, blocking=True, timeout=1)
        logger.debug(f"Getting command status data: {command.__dict__}")
        return response

    def Data_GetSSAlgoSet(self):
        command = self._build_command(ModbusRequestType.READ, OM_SS_REG_ADDR+OM_SS_ALGO_SET_OFF, count=OM_SS_ALGO_SET_LEN)
        response = self.modbus_worker.send_request(command, blocking=True, timeout=1)
        logger.debug(f"Getting SS algo set data: {command.__dict__}")
        if "data" in response:
            response["data"] = OM_SS_parse_AlgoSet(response["data"])
        return response

    def Data_ReadTemperature(self):
        """
        Reads the current temperature from the device.
        Returns:
            dict: { "temperatures": list[float], "error": ... }
        """
        command = self._build_command(ModbusRequestType.READ, OM_CMD_REG_ADDR+OM_TEMP_OFF, count=OM_TEMP_LEN)
        response = self.modbus_worker.send_request(command, blocking=True, timeout=1)
        logger.debug(f"Getting temperature data: {command.__dict__}")
        if "data" in response:
            response["data"] = OM_SS_parse_Temperature(response["data"])
        return response


    def _CANWrp_ExecCmd(self, VarID: int = 14, Offset : int = 0, RTR: int = 1, data: list = [], DLen: int = 0, silent=False):
        pack = OM_build_CANWrp_WriteWrappedCmd(VarID=VarID, Offset=Offset, RTR=RTR, data=data, DLen=DLen)
        registers = PackToRegisters(pack=pack)

        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, registers=registers)
        if not silent:
            logger.debug(f"Sending CANEm command: {command.__dict__}")
        response = self.modbus_worker.send_request(command, silent=silent)
        if "error" in response:
            return {"error": response["error"]}

        command = self._build_command(ModbusRequestType.READ, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, count=OM_CAN_STR_LEN)
        response = self.modbus_worker.send_request(command, timeout=1, silent=silent)
        if not silent:
            logger.debug(f"Reading CANEm status: {command.__dict__}")
        if "data" in response:        
            resp_pack = RegistersToPack(response["data"])
            CANNum, TypeID, DLen, data_resp = OM_Parse_CANEmWrap(resp_pack)
            response["data"] = {"CANNum" : CANNum, "TypeID" : TypeID, "DLen" : DLen, "data" : data_resp}
        return response

    
    def CANWrp_ReadFlashFrag(self, offset=0):
        response = self._CANWrp_ExecCmd(Offset=offset, RTR = 1)
        if "data" in response:
            CANNum, TypeID, DLen, data_resp = response["data"].values()
            response["data"] = data_resp

        return response

    def CANWrp_ReadCB(self, silent=False):
        response = self._CANWrp_ExecCmd(Offset = 0x00080000, RTR = 1, silent=silent)
        if "data" in response:
            CANNum, TypeID, DLen, data_resp = response["data"].values()
            parsed_data = OM_ParseFlashStruct(data=data_resp, type=FlashCB_Type.INFO)
            response["data"] = parsed_data
        return response



    def Blt_SetPref(self, pref: int = 0):
        int_pack = OM_build_BltSetPref(pref)
        pack = OM_build_CANWrp_WriteWrappedCmd(VarID=14, Offset=0x00080000, RTR=0, data=int_pack, DLen=len(int_pack))
        registers = PackToRegisters(pack=pack)

        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, registers=registers)
        logger.debug(f"Sending CANEm command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        if "error" in response:
            return {"error": response["error"]}

        response = self._CANWrp_ExecCmd(Offset = 0x00080000, RTR = 1)
        if "data" in response:
            CANNum, TypeID, DLen, data_resp = response["data"].values()
            parsed_data = OM_ParseFlashStruct(data=data_resp, type=FlashCB_Type.INFO)
            if not "error" in response:
                if (int.from_bytes(parsed_data["Status"], "little") & 0x80) != 0x00:
                    response["Status"] = "Error"
                else:
                    response["Status"] = "Ok"

            response["data"] = parsed_data
        return response

    def Blt_CheckImgValid(self, part = 0):
        int_pack = OM_build_BltCheckImgValid(part)
        pack = OM_build_CANWrp_WriteWrappedCmd(VarID=14, Offset=0x00080000, RTR=0, data=int_pack, DLen=len(int_pack))
        registers = PackToRegisters(pack=pack)

        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, registers=registers)
        logger.debug(f"Sending CANEm command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        if "error" in response:
            return {"error": response["error"]}

        response = self._CANWrp_ExecCmd(Offset = 0x00080000, RTR = 1)
        if "data" in response:
            CANNum, TypeID, DLen, data_resp = response["data"].values()
            parsed_data = OM_ParseFlashStruct(data=data_resp, type=FlashCB_Type.INFO)
            if not "error" in response:
                if (int.from_bytes(parsed_data["Status"], "little") & 0x80) != 0x00:
                    response["Status"] = "Error"
                else:
                    response["Status"] = "Ok"

            response["data"] = parsed_data
        return response

    def Blt_EraseSector(self, sector = 7):
        int_pack = OM_build_BltEraseSector(sector)
        pack = OM_build_CANWrp_WriteWrappedCmd(VarID=14, Offset=0x00080000, RTR=0, data=int_pack, DLen=len(int_pack))
        registers = PackToRegisters(pack=pack)

        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, registers=registers)
        logger.debug(f"Sending CANEm command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        if "error" in response:
            return {"error": response["error"]}

        time.sleep(5)

        response = self._CANWrp_ExecCmd(Offset = 0x00080000, RTR = 1)
        if "data" in response:
            CANNum, TypeID, DLen, data_resp = response["data"].values()
            parsed_data = OM_ParseFlashStruct(data=data_resp, type=FlashCB_Type.INFO)
            if not "error" in response:
                if (int.from_bytes(parsed_data["Status"], "little") & 0x80) != 0x00:
                    response["Status"] = "Error"
                else:
                    response["Status"] = "Ok"

            response["data"] = parsed_data
        return response
    

    def Blt_EraseHalf(self):
        int_pack = OM_build_BltEraseSecondPart()
        pack = OM_build_CANWrp_WriteWrappedCmd(VarID=14, Offset=0x00080000, RTR=0, data=int_pack, DLen=len(int_pack))
        registers = PackToRegisters(pack=pack)

        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, registers=registers)
        logger.debug(f"Sending CANEm command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        if "error" in response:
            return {"error": response["error"]}

        time.sleep(5)

        response = self._CANWrp_ExecCmd(Offset = 0x00080000, RTR = 1)
        if "data" in response:
            CANNum, TypeID, DLen, data_resp = response["data"].values()
            parsed_data = OM_ParseFlashStruct(data=data_resp, type=FlashCB_Type.INFO)
            if not "error" in response:
                if (int.from_bytes(parsed_data["Status"], "little") & 0x80) != 0x00:
                    response["Status"] = "Error"
                else:
                    response["Status"] = "Ok"

            response["data"] = parsed_data
        return response
    

    def Blt_CheckCRC(self, img:int = 0, file_path=''):
        int_pack = OM_build_BltCheckCRC(img=img, FW_path=file_path)
        if int_pack is None:
            return {'error': 'File error'}

        pack = OM_build_CANWrp_WriteWrappedCmd(VarID=14, Offset=0x00080000, RTR=0, data=int_pack, DLen=len(int_pack))
        registers = PackToRegisters(pack=pack)

        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, registers=registers)
        logger.debug(f"Sending CANEm command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        if "error" in response:
            return {"error": response["error"]}

        response = self._CANWrp_ExecCmd(Offset = 0x00080000, RTR = 1)
        if "data" in response:
            CANNum, TypeID, DLen, data_resp = response["data"].values()
            parsed_data = OM_ParseFlashStruct(data=data_resp, type=FlashCB_Type.INFO)
            if not "error" in response:
                if (int.from_bytes(parsed_data["Status"], "little") & 0x80) != 0x00:
                    response["Status"] = "Error"
                else:
                    response["Status"] = "Ok"

            response["data"] = parsed_data
        return response
    

    def Blt_FixValid(self, img:int = 0):
        int_pack = OM_build_BltFixValidImg(img=img)
        if int_pack is None:
            return {'error': 'File error'}

        pack = OM_build_CANWrp_WriteWrappedCmd(VarID=14, Offset=0x00080000, RTR=0, data=int_pack, DLen=len(int_pack))
        registers = PackToRegisters(pack=pack)

        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, registers=registers)
        logger.debug(f"Sending CANEm command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        if "error" in response:
            return {"error": response["error"]}

        response = self._CANWrp_ExecCmd(Offset = 0x00080000, RTR = 1)
        if "data" in response:
            CANNum, TypeID, DLen, data_resp = response["data"].values()
            parsed_data = OM_ParseFlashStruct(data=data_resp, type=FlashCB_Type.INFO)
            if not "error" in response:
                if (int.from_bytes(parsed_data["Status"], "little") & 0x80) != 0x00:
                    response["Status"] = "Error"
                else:
                    response["Status"] = "Ok"

            response["data"] = parsed_data
        return response
    
    def Blt_Restart(self):
        int_pack = OM_build_BltRestart()
        if int_pack is None:
            return {'error': 'File error'}

        pack = OM_build_CANWrp_WriteWrappedCmd(VarID=14, Offset=0x00080000, RTR=0, data=int_pack, DLen=len(int_pack))
        registers = PackToRegisters(pack=pack)

        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, registers=registers)
        logger.debug(f"Sending CANEm command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        if "error" in response:
            return {"error": response["error"]}
        
        return {'data': 'Cmd writen'}

    def Blt_CopyAndGo(self, file_path=''):
        int_pack = OM_build_CopyAndGo(FW_path=file_path)
        if int_pack is None:
            return {'error': 'File error'}

        pack = OM_build_CANWrp_WriteWrappedCmd(VarID=14, Offset=0x00080000, RTR=0, data=int_pack, DLen=len(int_pack))
        registers = PackToRegisters(pack=pack)

        command = self._build_command(ModbusRequestType.WRITE_MULTY, OM_BOOT_REG_ADDR+OM_CAN_STR_OFF, registers=registers)
        logger.debug(f"Sending CANEm command: {command.__dict__}")
        response = self.modbus_worker.send_request(command)
        return response

    def Blt_UploadFW(self, image: int, file: str):
        """
        Uploads firmware to the device.

        Args:
            image (int): 0 for main, 1 for reserve.
            file (str): Path to the firmware binary file.

        Returns:
            dict: Result of the upload process.
        """
        # 1. Open file, extract CRC and data
        try:
            file_info, file_content = analyze_bin_file(file)
            if file_info is None or file_content is None:
                return {"error": "File error or CRC/size not found"}
        except Exception as e:
            return {"error": f"File open/analyze error: {e}"}

        fw_size = file_info.get("FW_size", 0)
        fw_crc = file_info.get("CRC", 0)
        file_size = file_info.get("file_size", 0)
        if fw_size == 0:
            return {"error": "FW size is zero"}
        fw_data = file_content

        # 2. Get module's currently running block, compare with uploading block: if the same - error.
        cb_resp = self.CANWrp_ReadCB()
        if "data" not in cb_resp:
            return {"error": "Failed to read control block"}
        current_block = int.from_bytes(cb_resp["data"].get("CurrentBlock", None))
        if current_block is None:
            return {"error": "CurrentBlock not found in CB"}
        if current_block == image:
            return {"error": "Cannot upload to currently running image"}
 
        # 3. Set starting address as 0x00 cause Blt takes current FW addr and maps second FW to 0x00 addr.
        start_addr = 0x00

        # 4. Iterate over file bytes, make a command to write 8 bytes of file data.
        # 5. On each 128-byte written: read control block and check status. If status is incorrect - retry writing last 128 byte block
        chunk_size = 8
        block_size = 128
        total_len = len(fw_data)
        if(total_len % chunk_size) != 0:
            return {"error": "File size is not a multiple of 8 bytes"}
        if(total_len != file_size):
            return {"error": "File size does not match the expected size"}
        offset = 0
        retry_limit = 3

        logger.info(f"Starting firmware upload: {file}, size: {total_len} bytes")
        with tqdm(total=total_len, desc="FW upload", unit="B") as pbar:
            while offset < total_len:
                block = fw_data[offset:offset + block_size]
                block_offset = 0
                retries = 0
                while block_offset < len(block):
                    chunk = block[block_offset:block_offset + chunk_size]
                    # Pad chunk if less than 8 bytes
                    if len(chunk) < chunk_size:
                        logger.debug(f"Padding chunk at offset {offset + block_offset}: {chunk}")
                        chunk = chunk + b'\xFE' * (chunk_size - len(chunk))
                    # Prepare CAN wrapped command
                    pack = OM_build_CANWrp_WriteWrappedCmd(
                        VarID=14,
                        Offset=start_addr + offset + block_offset,
                        RTR=0,
                        data=list(chunk),
                        DLen=len(chunk)
                    )
                    registers = PackToRegisters(pack=pack)
                    command = self._build_command(
                        ModbusRequestType.WRITE_MULTY,
                        OM_BOOT_REG_ADDR + OM_CAN_STR_OFF,
                        registers=registers
                    )
                    response = self.modbus_worker.send_request(command, silent=True)
                    if "error" in response:
                        logger.error(f"Write error at offset {offset + block_offset}: {response['error']}")
                        return {"error": f"Write error at offset {offset + block_offset}: {response['error']}"}
                    block_offset += chunk_size
                    pbar.update(chunk_size)
                time.sleep(0.1)
                # After each 128 bytes, check control block status
                for _ in range(retry_limit):
                    cb_resp = self.CANWrp_ReadCB(silent=True)
                    if "data" in cb_resp:
                        status = cb_resp["data"].get("Status", 0)
                        # 0x80 is error, 0x10 is OK
                        if (int.from_bytes(status) & 0x80) == 0:
                            break  # OK
                    retries += 1
                    if retries >= retry_limit:
                        logger.error(f"Write failed at offset {offset}, status: {cb_resp}")
                        return {"error": f"Write failed at offset {offset}, status: {cb_resp}"}
                    time.sleep(0.2)
                offset += block_size

        logger.info("Firmware upload complete, verifying CRC and validity...")
        # 6. Once file content is loaded - check FW CRC and Valid.
        check_crc = self.Blt_CheckCRC(img=image, file_path=file)
        if 'Error' in check_crc:
            logger.error(f"CRC check failed: {check_crc['error']}")
            return {"error": f"CRC check failed: {check_crc['error']}"}
        # check_valid = self.Blt_CheckImgValid(part=image)
        # if 'Error' in check_valid:
        #     logger.error(f"Valid check failed: {check_valid['error']}")
        #     return {"error": f"Valid check failed: {check_valid['error']}"}

        logger.info("Firmware upload successful!")
        return {
            "status": "success",
            "CRC_check": check_crc
        }
    
    def Read_SS_Grayscale_Photo(self):
        """
        Reads the full 480x480x2 grayscale image from the device.
        Returns:
            dict: { "data": 2D list [480][480] of uint16, "raw": bytes, "error": ... }
        """
        logger.info("Starting grayscale photo readout...")
        lines = OM_SS_PHOTO_HGHT
        parts_per_line = OM_SS_LINE_PARTS
        image = np.zeros((OM_SS_PHOTO_HGHT, OM_SS_PHOTO_WDTH), dtype=np.uint16)
        raw_bytes = bytearray()
        for line in tqdm(range(lines), desc="Grayscale photo", unit="line"):
            line_bytes = bytearray()
            for part in range(parts_per_line):
                addr = OM_SS_ImgLinePartAddr(line=line, part=part)
                command = self._build_command(ModbusRequestType.READ, addr, count=OM_SS_PX_PER_PT)
                resp = self.send_modbus(command, timeout=2, silent=True)
                if "error" in resp:
                    logger.error(f"Error reading grayscale photo at line {line}, part {part}: {resp['error']}")
                    return {"error": resp["error"]}
                regs = resp["data"]
                part_bytes_data = RegistersToPack(regs)
                line_bytes.extend(part_bytes_data)
            for px in range(480):
                val = int.from_bytes(line_bytes[px*2:px*2+2], "little")
                image[line, px] = val
            raw_bytes.extend(line_bytes)
        return {"data": image.tolist(), "raw": bytes(raw_bytes)}

    def Read_SS_Grayscale_Lines(self, start_line: int, end_line: int):
        """
        Reads lines [start_line, end_line) (0-based, end exclusive) of the grayscale image.
        Returns:
            dict: { "data": 2D list, "raw": bytes, "error": ... }
        """
        logger.info(f"Starting grayscale lines readout: {start_line} to {end_line}...")
        if start_line < 0 or end_line > OM_SS_PHOTO_HGHT or start_line >= end_line:
            return {"error": "Invalid line range"}
        parts_per_line = OM_SS_LINE_PARTS
        result = np.zeros((end_line - start_line, OM_SS_PHOTO_WDTH), dtype=np.uint16)
        raw_bytes = bytearray()
        for idx, line in tqdm(enumerate(range(start_line, end_line)), total=(end_line - start_line), desc="Grayscale lines", unit="line"):
            line_bytes = bytearray()
            for part in range(parts_per_line):
                addr = OM_SS_ImgLinePartAddr(line=line, part=part)
                command = self._build_command(ModbusRequestType.READ, addr, count=OM_SS_PX_PER_PT)
                resp = self.send_modbus(command, timeout=2, silent=True)
                if "error" in resp:
                    logger.error(f"Error reading grayscale line {line}, part {part}: {resp['error']}")
                    return {"error": resp["error"]}
                regs = resp["data"]
                part_bytes_data = RegistersToPack(regs)
                line_bytes.extend(part_bytes_data)
            for px in range(480):
                val = int.from_bytes(line_bytes[px*2:px*2+2], "little")
                result[idx, px] = val
            raw_bytes.extend(line_bytes)
        logger.info("Grayscale lines readout complete.")
        return {"data": result.tolist(), "raw": bytes(raw_bytes)}

    def Read_Thermal_Photo(self):
        """
        Reads the full 32x24 float thermal image from the device.
        Returns:
            dict: { "data": 2D list [24][32] of float, "raw": bytes, "error": ... }
        """
        logger.info("Starting thermal photo readout...")
        lines = OM_HS_PHOTO_HGHT
        pixels_per_line = OM_HS_PHOTO_WDTH
        result = np.zeros((OM_HS_PHOTO_HGHT, OM_HS_PHOTO_WDTH), dtype=np.float32)
        raw_bytes = bytearray()
        for line in tqdm(range(lines), desc="Thermal photo", unit="line"):
            addr = OM_HS_ImgLineAddr(line)
            command = self._build_command(ModbusRequestType.READ, addr, count=OM_HS_PHOTO_WDTH*2)
            resp = self.send_modbus(command, timeout=2, silent=True)
            if "error" in resp:
                logger.error(f"Error reading thermal photo at line {line}: {resp['error']}")
                return {"error": resp["error"]}
            regs = resp["data"]
            line_bytes = bytearray(RegistersToPack(regs))
            floats = [struct.unpack("<f", line_bytes[i*4:i*4+4])[0] for i in range(pixels_per_line)]
            result[line, :] = floats
            raw_bytes.extend(line_bytes)
        logger.info("Thermal photo readout complete.")
        return {"data": result.tolist(), "raw": bytes(raw_bytes)}

