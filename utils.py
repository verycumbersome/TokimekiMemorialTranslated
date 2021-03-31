#!/usr/bin/env python3
import os
import re
import mmap

from textwrap import wrap
from google_trans_new import google_translator

translator = google_translator()

def clean_seq(seq):
    seq = str(seq).lower()
    seq = seq.replace("71", "")
    seq = seq.replace("20", "")
    seq = seq.replace(" ", "")
    seq = seq.replace("8200", "")
    seq = seq.replace("00", "")

    return seq


def clean_byte_seq(seq):
    enc_seq = []
    for l in re.split(b'(8142|8148|20)', seq[:-1]):
        enc_seq.append(l.decode("shift-jis", "ignore")[(len(l) % 4):])

    seq = "".join(enc_seq)

    return seq


def read_hex(hexf, offset = 0, translate = False):
    # for offset in range(4):
    out = []
    for k in [hexf[c:c+4] for c in range(offset, len(hexf), 4)]:
        try:
            kana = bytes.fromhex(k).decode("shift-jis", "ignore")
            out.append(kana)

        except:
            continue

    out = ''.join(out)

    if translate:
        try:
            out = translator.translate(out, lang_tgt='en')
        except:
            print("Translation error")

    return out


if __name__=="__main__":
    text = input()
    for t in text.split(" 0 "):
        print(read_hex(clean_seq(t), translate = False))
