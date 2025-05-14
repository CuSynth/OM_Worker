import struct
import ctypes
from enum import Enum
from OM_registers import *


OM_CMD_TAKE_HS      = 0x21

class TypeID_t(ctypes.BigEndianStructure):
    _fields_ = [
        ("Dev",  ctypes.c_uint32, 4),
        ("Var",  ctypes.c_uint32, 4),
        ("Off",  ctypes.c_uint32, 21),
        ("res1", ctypes.c_uint32, 1),
        ("RTR",  ctypes.c_uint32, 1),
        ("res2", ctypes.c_uint32, 1)
    ]

class FlashCB_Type(Enum):
    INFO = 1
    CTRL = 2


def OM_BuildCmd_Reboot():
    cmd = 0xFE
    DLen = 0x01
    data = [0x01, 0x30]
    
    pack = [(cmd & 0xFF), ((cmd >> 8) & 0xFF), (DLen & 0xFF), ((DLen >> 8) & 0xFF)] 
    pack.extend(data)

    return pack



def OM_build_cmd_SS_take():
    return [0x21]

def OM_build_set_DevID(ID : int = 2):
    cmd = 0x13
    DLen = 0x01
    data = [ID]
    
    pack = [(cmd & 0xFF), ((cmd >> 8) & 0xFF), (DLen & 0xFF), ((DLen >> 8) & 0xFF)] 
    pack.extend(data)

    return pack

def OM_SS_parse(registers: list = []):
    if(len(registers) != OM_SS_DATA_LEN):
        return None

    hex_array = bytearray()
    for i in range(0, 14, 2):
        double_reg = (registers[i] << 16) | (registers[i+1])
        hex_array.extend(struct.pack(">I", double_reg))
    
    floats = struct.unpack("<fffffff", hex_array)
    status = struct.unpack("<H", struct.pack(">H",registers[-2]))[0]

    return {"X" : floats[0], "Y" : floats[1], "Z" : floats[2],
                "X_pt" : floats[3], "Y_pt" : floats[4], 
                "Zen" : floats[5], "Azt" : floats[6],
                "Status" : status}

def OM_parse_DevID(registers: list = []):
    if len(registers) != OM_DEV_ID_LEN:
        return None

    hex_array = bytearray()
    hex_array.extend(struct.pack(">H", registers[0]))
    ID = struct.unpack("<H", hex_array)[0]

    return {"DevID" : ID}
    


def OM_build_CANEm_WriteWrappedCmd(CAN_num: int = 1, DevID: int = 0, VarID: int = 14, Offset : int = 0, RTR: int = 1, data: list = [], DLen: int = 0):
    RTR = RTR & 0x01
    if CAN_num > 2 or CAN_num < 0 or VarID != 14:
        return None
    if len(data) == 0 and RTR != 1:
        return None
    
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
        return None


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
    if len(data) != 8:
        return None
    
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
