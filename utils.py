import os
import re
import mmap

from textwrap import wrap
from google_trans_new import google_translator

translator = google_translator()

def clean_seq(seq):
    print("SEQ", seq)
    seq = str(seq).lower()
    seq = seq.replace("71", "")
    seq = seq.replace("20", "")
    seq = seq.replace(" ", "")
    seq = seq.replace("8200", "")
    seq = seq.replace("00", "")

    return seq


def read_hex(hexf, translate = False):
    # for i in range(4):
    i = 0
    out = []
    print(hexf)
    print([hexf[c:c+4] for c in range(i, len(hexf), 4)])
    for k in [hexf[c:c+4] for c in range(i, len(hexf), 4)]:
        try:
            kana = bytes.fromhex(k).decode("shift_jisx0213", "ignore")
            out.append(kana)

        except:
            continue

    out = ''.join(out)

    if translate:
        out_trans = translator.translate(out, lang_tgt='en')
        print("Translated:", out_trans)

    print("Original:", out)
    print()


def read_file_addr(filename, addr):
    f_ptr = os.open(filename, os.O_RDWR)

    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)
    mm.seek(addr)
    line = mm.readline()

    out = line.decode("shift-jis", "ignore")
    # out = translator.translate(out, lang_tgt='en')

    return out


if __name__=="__main__":
    text = input()
    for t in text.split(" 0 "):
        read_hex(clean_seq(t), translate = True)
