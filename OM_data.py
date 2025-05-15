import struct
import ctypes
from enum import Enum
from OM_registers import *


OM_CMD_TAKE_HS      = 0x21

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



def OM_FWVer_parse(Pack: list = []):
    if len(Pack) != OM_FW_VER_LEN * 2:
        return None
    
    patch, minor, major  = struct.unpack("<HHH", bytes(Pack))
    return  f"{major}.{minor}.{patch}"
    # return {"Major" : major, "Minor" : minor, "Patch" : patch}

def OM_MnfID(Pack: list):
    return f"{Pack[3]:02x}{Pack[2]:02x}{Pack[1]:02x}{Pack[0]:02x}"



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





