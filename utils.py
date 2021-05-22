#!/usr/bin/env python3
"""
Basic utilities across all other modules
"""

import os
import re
import mmap
import json

import numpy as np

from textwrap import wrap
from google_trans_new import google_translator

path = os.path.dirname(__file__)
translator = google_translator()



def handle_dup(seq):
    """Takes string sequence and checks for duplicates"""
    dup = seq.split(b" ")
    dup = sum([dup[c] == dup[(c+1)%len(dup)] for c in range(len(dup))])

    if dup > 10:
        seq = b"".join(seq.split(b" ")[::2])

    return seq


def encode_english(seq):
    """encodes an english sequence into equivilant english shift-jis chars"""
    enc = []
    out = []
    counter = 0
    return_flag = False

    for c in seq:
        counter += 1

        if re.findall("[a-zA-Z]", c):
            offset = 0x821F # Shift JIS offset for capital english

        if re.findall("[a-z]", c):
            offset = 0x8220 # Shift JIS offset for lower-case english

        if c == ".":
            offset = 0x8114

        if c == " ":
            if return_flag:
                enc.append(0x20)
                return_flag = False
                continue

            offset = 0x8120

        if c == "(" or c == ")":
            offset = 0x8141

        if counter % 12 == 0:
            return_flag = True

        # Split the english S.J hex and convert both halves to int
        c = hex(int(c.encode().hex(), 16) + offset)[2:]
        if len(c) == 4: # If char is 2 bytes 
            enc.append(int(c[:2], 16))
            enc.append(int(c[2:], 16))

        else:
            enc.append(int(c, 16))

        c = bytes.fromhex(c).decode("shift-jis", "ignore")

        out += c

    out = "".join(out)

    print(out)

    return enc


def check_validity(seq: str) -> int:
    """Returns proportion of valid shift-jis characters in a string"""
    valid = 0
    for c in seq:
        enc_char = int(c.encode("shift-jis", "ignore").hex(), 16)
        if 0x8140 < enc_char < 0x9FFC:
            valid += 1

    if len(seq):
        return valid / len(seq)

    return 0


def decode_seq(seq: bytes) -> str:
    """Encodes hex string into shift-jis ascii string"""
    # seq = seq[len(seq) % 4:]
    seq = max(seq.split(b"\x00"), key=len)

    enc_seq = []
    for s in re.split(b'(\x81\x42|\x81\x48|\x20)', seq):
        if len(s) >= 2:
            enc_seq.append(s[len(s) % 2:].decode("shift-jis", "ignore"))

    return("".join(enc_seq))


if __name__=="__main__":
    # text = input()

    text = "82 D3 81 5B 82 C1 81 41 94 E6 82 EA 82 BD 81 42 20 81 69 92 A9 91 81 82 AD 91 96 82 E9 82 CC 82 CD 81 41 20 8B 43 8E 9D 82 BF 82 AA 82 A2 82 A2 82 C8 82 A0 81 42 81 6A"

    # print(encode_english(text))
    for seq in text.split(" 0 "):
        seq = seq.replace("47", "")
        seq = seq.replace(" ", "")
        seq = bytes.fromhex(seq)

        seq = seq.decode("shift-jis", "ignore")
        # print(seq)

        seq = translator.translate(seq, lang_tgt="en")
        # print(seq)

        fp = open("pointer_table.json", "w")
        seq = encode_english(seq)

        out = {
            "0":seq
        }

        json.dump(
            out,
            fp
        )
