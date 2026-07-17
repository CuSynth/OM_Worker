import struct
import ctypes
from typing import Any
import numpy as np
from enum import Enum
from OM_registers import *
import pandas as pd

OM_CMD_SAVE_SET     = 0x01
OM_CMD_LOAD_SET     = 0x02

OM_CMD_SET_DEV_ID   = 0x13
OM_CMD_REBOOT       = 0xFE

OM_CMD_TAKE_SS      = 0x21
OM_CMD_EMUL_SS      = 0x22
OM_CMD_RST_SET_SS   = 0x23
OM_CMD_RST_CAL_SS   = 0x24

OM_CMD_TAKE_HS      = 0x31
OM_CMD_EMUL_HS      = 0x32
OM_CMD_RST_SET_HS   = 0x33
OM_CMD_SAVE_HSCAL   = 0x34
OM_CMD_LOAD_HS_CAL  = 0x35
OM_CMD_RESET_HS_CAL = 0x36

OM_CMD_TAKE_GAM     = 0x41
OM_CMD_RST_SET_GAM  = 0x44

OM_SS_PHOTO_WDTH    = 480
OM_SS_PHOTO_HGHT    = 480
OM_SS_PX_SIZE       = 2
OM_SS_LINE_PARTS    = 4
OM_SS_PX_PER_PT     = int(OM_SS_PHOTO_WDTH / OM_SS_LINE_PARTS)

OM_HS_PHOTO_WDTH    = 32
OM_HS_PHOTO_HGHT    = 24
OM_HS_PX_SIZE       = 4


HS_ALGO_SET_USE_CAL = (0x0001 << 0)

def OM_BuildCmd_SaveSet():
    return [OM_CMD_SAVE_SET]

def OM_BuildCmd_LoadSet():
    return [OM_CMD_LOAD_SET]

def OM_BuildCmd_Reboot():
    return [OM_CMD_REBOOT, 0x00, 0x01, 0x00, 0x01, 0x30]

def OM_build_cmd_SS_take():
    return [OM_CMD_TAKE_SS]

def OM_BuildCmd_ResetSetupSS():
    return [OM_CMD_RST_SET_SS]

def OM_BuildCmd_ResetCalSS():
    return [OM_CMD_RST_CAL_SS]

def OM_build_cmd_HS_take():
    return [OM_CMD_TAKE_HS]

def OM_BuildCmd_ResetSetupHS():
    return [OM_CMD_RST_SET_HS]

def OM_BuildCmd_SaveHSCal():
    return [OM_CMD_SAVE_HSCAL]

def OM_BuildCmd_LoadHSCal():
    return [OM_CMD_LOAD_HS_CAL]

def OM_BuildCmd_ResetHSCal():
    return [OM_CMD_RESET_HS_CAL]

def OM_build_cmd_GAM_take():
    return [OM_CMD_TAKE_GAM]

def OM_BuildCmd_ResetSetupGAM():
    return [OM_CMD_RST_SET_GAM]


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

def OM_HS_parse(registers: list = [], vector_cnt_exp=15):
    new_FW = True

    if new_FW:
        if(len(registers) != (1+1+vector_cnt_exp*3*1)):
            return None

        vect_amount = ( (registers[0] << 8) & 0xFF00 | (registers[0] >> 8) & 0x00FF )
        status =  ( (registers[1] << 8) & 0xFF00 | (registers[1] >> 8) & 0x00FF )
        # Structure is as folows: u16 - vect amount total, u16 - status, vector_cnt_exp x vectors (3xfloat each)
        hex_array = bytearray()
        for i in range(2, len(registers)):
            hex_array.extend(struct.pack(">H", registers[i]))

        int_16_arr = struct.unpack("<"+"h"*3*vector_cnt_exp, hex_array)

        floats = np.array(int_16_arr).reshape((-1,3)) / (0x01 << 14)
    else:
        if(len(registers) != (1+1+vector_cnt_exp*3*2)):
            return None

        vect_amount = ( (registers[0] << 8) & 0xFF00 | (registers[0] >> 8) & 0x00FF )
        status =  ( (registers[1] << 8) & 0xFF00 | (registers[1] >> 8) & 0x00FF )
        # Structure is as folows: u16 - vect amount total, u16 - status, vector_cnt_exp x vectors (3xfloat each)
        hex_array = bytearray()
        for i in range(2, len(registers), 2):
            double_reg = (registers[i] << 16) | (registers[i+1])
            hex_array.extend(struct.pack(">I", double_reg))

            
        floats = struct.unpack("<"+"f"*3*vector_cnt_exp, hex_array)

        floats = np.array(floats).reshape((-1,3))
    return {"Amount" : vect_amount, "status" : status, "data" : floats}

def OM_HSCalLineAddr(line:int):
    if line < 0 or line > 24:
        return OM_HS_CAL_ADDR

    return OM_HS_CAL_ADDR + line


def OM_CmdStat_parse(registers: list = []):
    if len(registers) != 2:
        return None

    cmd = struct.unpack("<H", struct.pack(">H",registers[0]))[0]
    stat = struct.unpack("<H", struct.pack(">H",registers[1]))[0]

    return {"Last command" : (f"0x%04x" % cmd), "status" : (f"0x%04x" % stat)}



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

def OM_HS_DataParse(registers: list = []):
    if len(registers) < 2+1*3*2:
        return None
    total_cnt = registers[0]
    res = registers[1]
    vect_regs = registers[2:]

    hex_array = bytearray()
    for i in range(0, len(vect_regs)):
        hex_array.extend(struct.pack(">H", vect_regs[i]))
    vect_read = int(len(hex_array)/3/4)

    components: tuple[Any, ...] = struct.unpack(f'<{"f" * vect_read * 3}', hex_array)
    vectors = np.array(components).reshape((-1,3))

    return {"Total vectors found" : total_cnt, "Vectors" : vectors}




def load_calibrated_vectors(csv_path, width=OM_HS_PHOTO_WDTH, height=OM_HS_PHOTO_HGHT):
    """Reads the calibration CSV (Var1=Y, Var2=X, Var3=x, Var4=y, Var5=z) into (height,width) grids."""
    df = pd.read_csv(csv_path, header=0, names=["Y", "X", "vx", "vy", "vz"])

    X = np.full((height, width), np.nan)
    Y = np.full((height, width), np.nan)
    Z = np.full((height, width), np.nan)

    for _, row in df.iterrows():
        yi = int(row["Y"])
        xi = int(row["X"])
        if 0 <= yi < height and 0 <= xi < width:
            X[yi, xi] = row["vx"]
            Y[yi, xi] = row["vy"]
            Z[yi, xi] = row["vz"]
        else:
            print(f"Warning: pixel (Y={yi}, X={xi}) is out of bounds for {height}x{width}, skipped.")

    n_missing = int(np.isnan(X).sum())
    if n_missing:
        print(f"Warning: {n_missing} pixel(s) missing in calibration CSV (left as NaN).")

    return X, Y, Z