FOOTER_SIZE = 560
HEADER_SIZE = 48
BLOCK_SIZE = 4096

TABLE_SEP = b"\x00\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00"
BIN_PATH = "/home/matthew/.local/share/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin"

# MEM_MIN = 0x6000000
# MEM_MAX = 0x6483510 + (HEADER_SIZE + BLOCK_SIZE + FOOTER_SIZE) * 600

MEM_MIN = 0x6480000
MEM_MAX = 0x6483510
