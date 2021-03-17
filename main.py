import re

from textwrap import wrap
from google_trans_new import google_translator

# From ADDRESS: 0x02A7Fa46

translator = google_translator()

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
        out = translator.translate(out, lang_tgt='en')
        print(f"{out}")


if __name__=="__main__":
    text = input()
    print(read_hex(text))

    # with open("hex.txt", "r") as hexf:
        # print (read_hex(hexf.read()))
