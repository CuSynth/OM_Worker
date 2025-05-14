

# Offsets and lengths are in 16bit registers!

# Direct cmd
OM_ADDR_DIRECT_CMD_FLAG = 0x8000

# Comand and status registers
OM_CMD_REG_ADDR     = 0x1000

OM_CMD_OFF          = 0

OM_STATUS_OFF       = 10
OM_STATUS_LEN       = 8

OM_FW_WER_OFF       = 20
OM_FW_WER_LEN       = 3

OM_CUR_REGION_OFF   = 23
OM_CUR_REGION_LEN   = 1

OM_MNF_ID_OFF       = 24
OM_MNF_ID_LEN       = 2

OM_TEMP_OFF         = 26
OM_TEMP_LEN         = 3

OM_DEV_ID_OFF       = 30
OM_DEV_ID_LEN       = 1

OM_GIT_HASH_OFF     = 32
OM_GIT_HASH_LEN     = 4

# Sun sensor registers
OM_SS_REG_ADDR      = 0x2000
OM_SS_DATA_OFF      = 0
OM_SS_DATA_LEN      = 16

OM_SS_EMUL_OFF      = 16
OM_SS_EMUL_LEN      = 16

OM_SS_MTX_SET_OFF   = 32
OM_SS_MTX_SET_LEN   = 14

OM_SS_ALGO_SET_OFF  = 46
OM_SS_ALGO_SET_LEN  = 24


# Horizon sensor registers
OM_HS_REG_ADDR      = 0x3000
OM_HS_DATA_OFF      = 0
OM_HS_DATA_LEN      = 194

OM_HS_MTX_SET_OFF   = 200
OM_HS_MTX_SET_LEN   = 6

OM_HS_ALGO_SET_OFF  = 206
OM_HS_ALGO_SET_LEN  = 8

OM_HS_EMUL_OFF      = 214
OM_HS_EMUL_LEN      = 8

# GAM registers
OM_GAM_REG_ADDR     = 0x4000
OM_GA_DATA_OFF      = 0
OM_GA_DATA_LEN      = 14

OM_MAG_DATA_OFF     = 14
OM_MAG_DATA_LEN     = 8

OM_GA_DESC_OFF      = 48
OM_GA_DESC_LEN      = 20

OM_MAG_DESC_OFF     = 68
OM_MAG_DESC_LEN     = 18


OM_BOOT_REG_ADDR    = 0xF000
OM_CAN_STR_OFF      = 0
OM_CAN_STR_LEN      = 8


if __name__ == "__main__":
    print("Started OM Registers descriptor")
    print(f"OM_CMD_REG_ADDR     = {hex(OM_CMD_REG_ADDR)}")
    print(f"OM_SS_REG_ADDR      = {hex(OM_SS_REG_ADDR)}")
    print(f"OM_HS_REG_ADDR      = {hex(OM_HS_REG_ADDR)}")
    print(f"OM_GAM_REG_ADDR     = {hex(OM_GAM_REG_ADDR)}")
    
    


    




