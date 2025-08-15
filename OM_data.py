import struct
import ctypes
from enum import Enum
from OM_registers import *


OM_CMD_SET_DEV_ID   = 0x13
OM_CMD_REBOOT       = 0xFE

OM_CMD_TAKE_SS      = 0x21
OM_CMD_TAKE_HS      = 0x31
OM_CMD_TAKE_GAM     = 0x41


OM_SS_PHOTO_WDTH    = 480
OM_SS_PHOTO_HGHT    = 480
OM_SS_PX_SIZE       = 2
OM_SS_LINE_PARTS    = 4
OM_SS_PX_PER_PT     = int(OM_SS_PHOTO_WDTH / OM_SS_LINE_PARTS)

OM_HS_PHOTO_WDTH    = 32
OM_HS_PHOTO_HGHT    = 24
OM_HS_PX_SIZE       = 4






def OM_BuildCmd_Reboot():
    cmd = OM_CMD_REBOOT
    DLen = 0x01
    data = [0x01, 0x30]
    
    pack = [(cmd & 0xFF), ((cmd >> 8) & 0xFF), (DLen & 0xFF), ((DLen >> 8) & 0xFF)] 
    pack.extend(data)

    return pack

def OM_build_cmd_SS_take():
    return [OM_CMD_TAKE_SS]

def OM_build_cmd_HS_take():
    return [OM_CMD_TAKE_HS]

def OM_build_cmd_GAM_take():
    return [OM_CMD_TAKE_GAM]

def OM_build_set_DevID(ID : int = 2):
    cmd = OM_CMD_SET_DEV_ID
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


def OM_GAM_parse(registers: list):
    if(len(registers) != OM_GAM_DATA_LEN):
        return None

    ret = {}
    
    GA_regs = registers[OM_GA_DATA_OFF:OM_GA_DATA_OFF+OM_GA_DATA_LEN]
    MAG_regs = registers[OM_MAG_DATA_OFF:OM_MAG_DATA_OFF+OM_MAG_DATA_LEN]

    hex_array = bytearray()
    for i in range(0, OM_GA_DATA_LEN, 2):
        double_reg = (GA_regs[i] << 16) | (GA_regs[i+1])
        hex_array.extend(struct.pack(">I", double_reg))

    gyro_dps = struct.unpack("<fff", hex_array[0:12])
    ret['G_dps'] = gyro_dps

    accel_G = struct.unpack("<fff", hex_array[12:24])
    ret['A_G'] = accel_G

    GA_temp = struct.unpack("H", hex_array[24:26])[0]
    ret['GA_temp'] = GA_temp

    GA_stat  = struct.unpack("h", hex_array[26:28])[0]
    ret['GA_stat'] = GA_stat


    hex_array = bytearray()
    for i in range(0, OM_MAG_DATA_LEN, 2):
        double_reg = (MAG_regs[i] << 16) | (MAG_regs[i+1])
        hex_array.extend(struct.pack(">I", double_reg))

    MGM_uT = struct.unpack("<fff", hex_array[0:12])
    ret['MGM_uT'] = MGM_uT
    
    MGM_temp = struct.unpack("H", hex_array[12:14])[0]
    ret['MGM_temp'] = MGM_temp

    MGM_stat  = struct.unpack("h", hex_array[14:16])[0]
    ret['MGM_stat'] = MGM_stat


    return ret

def OM_SS_parse_AlgoSet(registers: list = []):
    if len(registers) != OM_SS_ALGO_SET_LEN:
        return None

    hex_array = bytearray()
    for i in range(0, OM_SS_ALGO_SET_LEN):
        hex_array.extend(struct.pack(">H", registers[i]))

    # Parse them as 11x float and 2xU16
    algo_set = struct.unpack("<fffffffffffHH", hex_array)
    return {"Settings" : algo_set, "Hexed" : [f"0x{val:04X}" for val in hex_array]}



def OM_parse_DevID(registers: list = []):
    if len(registers) != OM_DEV_ID_LEN:
        return None

    hex_array = bytearray()
    hex_array.extend(struct.pack(">H", registers[0]))
    ID = struct.unpack("<H", hex_array)[0]

    return {"DevID" : ID}

def OM_parse_FWVer(registers: list = []):
    if len(registers) != OM_FW_VER_LEN:
        return None

    fix = (registers[0] >> 8) | ((registers[0] & 0x00FF) << 8)
    minr = (registers[1] >> 8) | ((registers[1] & 0x00FF) << 8)
    majr = (registers[2] >> 8) | ((registers[2] & 0x00FF) << 8)

    return {"FWVer" : ('%02d.%02d.%02d' % (majr, minr, fix))}

def OM_SS_parse_MtxSet(registers: list = []):
    if len(registers) != OM_SS_MTX_SET_LEN:
        return None

    hex_array = bytearray()
    for i in range(0, OM_SS_MTX_SET_LEN):
        hex_array.extend(struct.pack(">H", registers[i]))

    mtx = struct.unpack("<HHHHHHHHHHHHHH", hex_array)
    
    return {"Settings" : mtx, "Hexed" : [f"0x{val:04X}" for val in mtx]}


def OM_SS_parse_Temperature(registers: list = []):
    if len(registers) != OM_TEMP_LEN:
        return None
    
    hex_array = bytearray()
    for i in range(0, OM_TEMP_LEN):
        hex_array.extend(struct.pack(">H", registers[i]))

    temp = struct.unpack("<hhh", hex_array)
    return {"MCU": temp[0], "MGM": temp[1], "GA": temp[2]}


def OM_SS_ImgLinePartAddr(line: int, part: int):
    return (OM_SS_DIRECT_ADDR | ((line & 0x01FF) << 2) | (part & 0x03))

def OM_HS_ImgLineAddr(line:int):
    return (OM_HS_DIRECT_ADDR | (line & 0x3F))

def OM_HS_ImgClustLineAddr(line:int):
    return (OM_HS_DIRECT_CLUST_ADDR | (line & 0x3F))


