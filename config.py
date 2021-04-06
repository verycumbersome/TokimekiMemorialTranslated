MEM_MAX = 0x64FFFFF
MEM_MIN = 0x6362FD8
TOKIMEKI_PATH = "/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin"

TABLE_HEADER = """# start table is @hiragana
# make sure you view this in a font that contains U+3099/U+309A

@main

/00=[end]
"""

ATLAS_HEADER = """//GAME NAME:        TokiMeki Memorial

#VAR(dialog, TABLE)
#ADDTBL("game.tbl", dialog)
#ACTIVETBL(dialog) // Activate this block's starting TABLE

#VAR(ptr, CUSTOMPOINTER)
#CREATEPTR(ptr, "LINEAR", $0, 32)

#SETPTRFILE(“patch.bin”)
#JMP($8F510) // Jump to insertion point

#WRITE(ptr, $29D71E50)
ｗｈａｔ　ｓｈｏｕｌｄ　ｉ ｄｏ　ｔｏｄａｙ[end]
"""
