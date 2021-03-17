import re
from textwrap import wrap

# From ADDRESS: 0x02A7Fa46
# text = "82CD 8141 82C7 82A4 8148 0000 82A2 82E2 829F 8141 97C7 82A9 82C1 82BD 82E6 8142 967B 9396 82C9 8142 0000 0000 97C7 82A9 82C1 82BD 8142 208B 4382 C993 FC82 C182 C482 E082 E782 A682 C481 6381 4200 0000 82B3 82A0 82C4 8141 2082 BB82 EB82 BB82 EB8B 4182 EB82 A482 A982 C881 4200 0000 82E0 82A4 8B41 82C1 82BF 82E1 82A4 82CC 8148 2082 E082 C182 C682 E482 C182 AD82 E882 B582 C420 82A2 82AF 82CE 82A2 82A2 82CC 82C9 8142 0000 82A0 82F1 82DC 82E8 8141 82A2 82E9 82C6 8141 2091 BC82 CC90 6C82 CC8E D796 8282 C982 C882 E982 A982 E781 4200 82BB 82A4 8163 8142 2082 A082 E882 AA82 C682 A481 4197 8882 C482 AD82 EA82 C481 6381 4220 82BB 82EA 82B6 82E1 82A0 8141 82B3 82E6 82C8 82E7 8142 0000 4881 1E80 5881 1E80"

def read_hex(hexf):
    out = []
    for k in hexf.split():
        if k[0] == "8":
            try:
                kana = bytes.fromhex(k).decode("shift_jisx0213")
                out.append(kana)

            except:
                pass

    return ''.join(out)

if __name__=="__main__":
    with open("hex.txt", "r") as hexf:
        print (read_hex(hexf.read()))
    # print(read_hex(text))

