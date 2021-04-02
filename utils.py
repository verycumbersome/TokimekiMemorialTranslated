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
    seq = max(seq.split(b"\x00"), key=len)

    enc_seq = []
    # for s in re.split(b'(\x81\x42|\x81\x48|\x20|\x71)', seq):
    for s in re.split(b'(\x81\x42|\x81\x48|\x20)', seq):
        if (len(s) >= 2):
            enc_seq.append(s[len(s) % 2:].decode("shift-jis", "ignore"))

    return("".join(enc_seq))


if __name__=="__main__":
    text = input()
    for seq in text.split(" 0 "):
        seq = seq.replace("47", "")
        seq = seq.replace(" ", "")
        seq = bytes.fromhex(seq)

        print(seq.decode("shift-jis", "ignore"))

        print(encode_seq(seq))
