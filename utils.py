#!/usr/bin/env python3
import os
import re
import mmap

from textwrap import wrap
from google_trans_new import google_translator

translator = google_translator()


def encode_seq(seq):
    """Encodes hex string into shift-jis ascii string"""
    # seq = seq[len(seq) % 4:]
    enc_seq = []
    for s in re.split(b'(\x81\x42|\x81\x48|\x20|\x00)', seq):
        if (len(s) >= 2):
            enc_seq.append(s[len(s) % 2:].decode("shift-jis", "ignore"))

    return("".join(enc_seq))


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
    for seq in text.split(" 0 "):
        seq = str(seq).lower()
        seq = seq.replace("71", "")
        seq = seq.replace("20", "")
        seq = seq.replace(" ", "")
        seq = seq.replace("8200", "")
        seq = seq.replace("00", "")

        print(read_hex(seq, translate = False))
