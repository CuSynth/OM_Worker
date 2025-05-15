import struct
import ctypes
from enum import Enum
import zlib
import os
from OM_registers import *
from CRC_lib import crc32_stm

class FlashCB_Type(Enum):
    INFO = 1
    CTRL = 2

class TypeID_t(ctypes.BigEndianStructure):
    _fields_ = [
        ("Dev",  ctypes.c_uint32, 4),
        ("Var",  ctypes.c_uint32, 4),
        ("Off",  ctypes.c_uint32, 21),
        ("res1", ctypes.c_uint32, 1),
        ("RTR",  ctypes.c_uint32, 1),
        ("res2", ctypes.c_uint32, 1)
    ]


def OM_build_CANWrp_WriteWrappedCmd(CAN_num: int = 1, DevID: int = 0, VarID: int = 14, Offset : int = 0, RTR: int = 1, data: list = [], DLen: int = 0):
    RTR = RTR & 0x01
    if CAN_num > 2 or CAN_num < 0 or VarID != 14:
        return []
    if len(data) == 0 and RTR != 1:
        return []
    
    Offset = Offset & ((1 << 21) - 1)
    type_ID = (DevID << 28) | (VarID << 24) | (Offset << 3) | ((RTR << 1) & 0x02)
    length  = max(DLen, 8)
    pack = [CAN_num, 0x00, (type_ID & 0xFF), ((type_ID >> 8) & 0xFF), ((type_ID >> 16) & 0xFF), ((type_ID >> 24) & 0xFF), length, 0x00]

    if RTR == 1:
        pass
    else:
        data = data[0:length]
        pack.extend(data)
    return pack

def OM_Parse_CANEmWrap(pack: list = []):
    if len(pack) != OM_CAN_STR_LEN * 2:
        return []


    unpacked = struct.unpack("<ccIHcccccccc", bytes(pack))
    CANNum      = unpacked[0]
    TypeID_val  = unpacked[2]
    DLen        = unpacked[3]
    data        = unpacked[4:]

    TypeID = TypeID_t()
    struct.pack_into('!I', TypeID, 0, TypeID_val)

    return CANNum, TypeID, DLen, data


def OM_ParseFlashStruct_Ctrl(data: list = []):
    if len(data) != 8:
        return None
    
    size = (data[2] << 16) | (data[1] << 8) | data[0]
    cmd = data[3]
    crc = (data[7] << 24) | (data[6] << 16) | (data[5] << 8) | data[4]

    return size, cmd, crc
    

def OM_ParseFlashStruct_Info(data: list = []):
    if len(data) != 8:
        return None
    
    Status = data[0]
    CurrentBlock = data[1]
    PrefBlock = data[2]
    ResetSrc = data[3]

    return Status, CurrentBlock, PrefBlock, ResetSrc

def OM_ParseFlashStruct(data: list, type: FlashCB_Type):
    DLen = len(data)
    if len(data) != 8:
        return {"error" : "DLen", "len": DLen, "data" : data}
    
    if type == FlashCB_Type.INFO:
        Status = data[0]
        CurrentBlock = data[1]
        PrefBlock = data[2]
        ResetSrc = data[3]
        return {"Status" : Status, "CurrentBlock" : CurrentBlock, "PrefBlock" : PrefBlock, "ResetSrc" : ResetSrc}
    elif type == FlashCB_Type.CTRL:
        size = (data[2] << 16) | (data[1] << 8) | data[0]
        cmd = data[3]
        crc = (data[7] << 24) | (data[6] << 16) | (data[5] << 8) | data[4]
        return {"Size" : size, "Cmd" : cmd, "CRC" : crc}
    else:
        return {"error" : "Unknown type"}


def OM_build_BltSetPref(pref: int):
    pref = pref & 0x01
    size = 0
    cmd = 0x0A | pref
    crc = 0

    pack = [(size & 0xFF), ((size >> 8) & 0xFF), ((size >> 16) & 0xFF), cmd, 
            (crc & 0xFF), ((crc >> 8) & 0xFF), ((crc >> 16) & 0xFF), ((crc >> 24) & 0xFF)]

    return pack

def OM_build_BltCheckImgValid(part: int):
    part = part & 0x01
    size = 0
    cmd = 0x06 | part
    crc = 0

    pack = [(size & 0xFF), ((size >> 8) & 0xFF), ((size >> 16) & 0xFF), cmd, 
            (crc & 0xFF), ((crc >> 8) & 0xFF), ((crc >> 16) & 0xFF), ((crc >> 24) & 0xFF)]

    return pack







def find_crc_and_size(file_content):
    """
    Finds the CRC32 and size within a byte string, mimicking the provided C code logic.

    Args:
        file_content (bytes): The content of the binary file as a byte string.

    Returns:
        dict: A dictionary containing the real size, written size, and CRC32 value if found,
              otherwise None.
    """
    addr = 0
    ret = -1
    calculated_crc = 0xFFFFFFFF  # Initialize CRC as in C code (CRC->CR = 1)
    file_size = len(file_content)
    
    prev_crc = 0
    CRC_match: bool= False
    Size_match: bool = False

    # Iterate through the file content in 4-byte chunks (assuming 32-bit words)
    for addr in range(0, file_size-4, 4):  # Equivalent to ptr < 0x00080000/4-1
        if calculated_crc == 0:
            CRC_match = True
            if addr == int.from_bytes(file_content[addr:addr+4], 'little')*4:
                addr += 4
                Size_match = True
            break
        prev_crc = calculated_crc
        calculated_crc: int = crc32_stm(file_content[addr:addr + 4], crc=calculated_crc) & 0xFFFFFFFF # Update CRC

    return {
        "file_size":    file_size,
        "FW_size":      addr,
        "crc":          prev_crc,
        "crc_match":    CRC_match,
        "size_match":   Size_match
    }


def analyze_bin_file(file_path):
    """
    Analyzes a binary file to extract CRC32, real size, and written size.

    Args:
        file_path (str): The path to the binary file.

    Returns:
        dict: A dictionary containing the real size, written size, and CRC32 value.
              Returns None if the file does not exist or if an error occurs during processing.
    """

    try:
        if not os.path.exists(file_path):
            raise Exception("Error: File not found at {file_path}")
        with open(file_path, "rb") as f:
            file_content = f.read()

        result = find_crc_and_size(file_content)
        return result
    
    except Exception as e:
        print(f"An error occurred: {e}")



def main():
    file_path = "FWs/OMMCU_v02_09_00_r.bin"  # Replace with the actual path
    result = analyze_bin_file(file_path)
    print(result)
    return

if __name__ == "__main__":
    main()

