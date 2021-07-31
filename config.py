# Memory
FOOTER_SIZE = 560
HEADER_SIZE = 48
BLOCK_SIZE = 4096

TABLE_SEP = b"\x00\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00"
BIN_PATH = "/home/matthew/.local/share/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin"

# MEM_MIN = 0x4000000
# MEM_MAX = 0x6000000

MEM_MIN = 0x6300000
MEM_MAX = 0x6483510
# MEM_MAX = 0x6483510 + (HEADER_SIZE + BLOCK_SIZE + FOOTER_SIZE) * 900


# Translation
START_SEQUENCE = "\nEnglish:"
# PROMPT = "Japanese: わたしは　にほんごがすこししかはなせません。\nEnglish: Unfortunately, I speak only a little Japanese..\n\nJapanese: やばい！あのジェットコースター、めっちゃたかい。\nEnglish: Oh my god! That roller coaster is super tall.\n\nJapanese: わぉ！宝くじ、1,000万円 当たった！\nEnglish: Wow! I won a lottery of 10,000,000 yen!\n\nJapanese: "
PROMPT = "Japanese: わぉ！宝くじ、1,000万円 当たった！\nEnglish: Wow! I won a lottery of 10,000,000 yen!\n\nJapanese:"
