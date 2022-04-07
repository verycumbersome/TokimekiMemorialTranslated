# Memory
FOOTER_SIZE = 560
HEADER_SIZE = 48
BLOCK_SIZE = 4096
TOTAL_BLOCK_SIZE = (HEADER_SIZE + BLOCK_SIZE + FOOTER_SIZE)

TABLE_SEP = b"\x00\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00"
BIN_PATH = "/home/mattjordan/Code/TokimekiMemorialTranslated/rom/Tokimeki Memorial - Forever with You (Japan) (PlayStation the Best) (Track 1).bin"

# MEM_MIN = 0x1000000
# MEM_MAX = 0x6000000

# MEM_MIN = 0x65EECC0
# MEM_MAX = 0x65EECC0 + (HEADER_SIZE + BLOCK_SIZE + FOOTER_SIZE) * 12

MEM_MIN = 0x647FDF0
MEM_MAX = 0x647FDF0 + TOTAL_BLOCK_SIZE * 14


# Translation
START_SEQUENCE = "\nEnglish:"
# PROMPT = "Japanese: わたしは　にほんごがすこししかはなせません。\nEnglish: Unfortunately, I speak only a little Japanese..\n\nJapanese: やばい！あのジェットコースター、めっちゃたかい。\nEnglish: Oh my god! That roller coaster is super tall.\n\nJapanese: わぉ！宝くじ、1,000万円 当たった！\nEnglish: Wow! I won a lottery of 10,000,000 yen!\n\nJapanese: "
PROMPT = "Japanese: わぉ！宝くじ、1,000万円 当たった！\nEnglish: Wow! I won a lottery of 10,000,000 yen!\n\nJapanese:"
