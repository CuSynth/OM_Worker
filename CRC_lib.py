from pathlib import Path
import struct

def generate_crc32_table(initial_polynome: int = 0x04C11DB7) -> list[int]:
    def bit_sum(byte: int) -> int:
        return [byte := (byte << 1) ^ initial_polynome
                if (byte & 0x80000000) else (byte << 1) for _ in range(8)][-1]

    return [bit_sum(i << 24) & 0xffffffff for i in range(256)]

crc_table: list[int] = generate_crc32_table()

def crc32_stm(bytes_arr: bytes, crc: int = 0xffffffff) -> int:
    """It is supposed that the length of firmware is % 4 = 0"""
    for num in struct.unpack(f'>{len(bytes_arr) // 4}I', bytes_arr):
        for i in [0, 8, 16, 24]:
            table_val: int = crc_table[0xFF & ((crc >> 24) ^ (num >> i))]
            crc = ((crc << 8) & 0xffffffff) ^ table_val
    return crc

def check_firmware_crc(bytes_arr: bytes) -> bool:
    crc: int = 0xFFFFFFFF
    for i in range(0, len(bytes_arr)-4, 4):
        if (crc == 0) and (i == int.from_bytes(bytes_arr[i:i+4], 'little')*4):
            return True
        crc = crc32_stm(bytes_arr[i:i+4], crc=crc)

    return False

if __name__ == '__main__':
    fw_path: Path = Path(__file__).parent / 'FWs' / 'OMMCU_v02_09_00_r.bin'
    with open(fw_path, 'rb') as fw:
        data: bytes = fw.read() #.rstrip(b'\xFE')
        print(check_firmware_crc(data))

    # fw_path: Path = Path(__file__).parent / 'FWs' / 'GRI00_32868_ADCS__v00_00_11_m.bin'
    # with open(fw_path, 'rb') as fw:
    #     data: bytes = fw.read() #.rstrip(b'\xFE')
    #     print(check_firmware_crc(data))
