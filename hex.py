import re
from textwrap import wrap

# From ADDRESS: 0x02A7Fa46

def read_hex(hexf):
    for i in range(4):
        hexf = hexf.replace(" ", "")

        out = []
        for k in [hexf[c:c+4] for c in range(i, len(hexf), 4)]:
            if ((k[0] == "8") or (k[0] == "9")):
                try:
                    kana = bytes.fromhex(k).decode("shift_jisx0213")
                    out.append(kana)

                except:
                    continue

        out = ''.join(out)
        print(out)

if __name__=="__main__":
    text = input()
    print(read_hex(text))

    # with open("hex.txt", "r") as hexf:
        # print (read_hex(hexf.read()))
