#!/usr/bin/env python3
import os
import re
import mmap

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
    enc = []
    for c in seq:
        if (re.findall("[a-zA-Z]", c)):
            offset = 0x821F
            if (re.findall("[a-z]", c)):
                offset = 0x8220

            c = hex(int(c.encode().hex(), 16) + offset)[2:]
            c = bytes.fromhex(c).decode("shift-jis", "ignore")

        enc += c

    enc = "".join(enc)

    print(enc.encode("shift-jis", "ignore").hex())

    return enc


def check_validity(seq):
    """Returns proportion of valid shift-jis characters in a string"""
    valid = 0
    for c in seq:
        enc_char = int(c.encode("shift-jis", "ignore").hex(), 16)
        if (0x8140 < enc_char < 0x9FFC):
            valid += 1

    if len(seq):
        return valid / len(seq)

    return 0


def decode_seq(seq):
    """Encodes hex string into shift-jis ascii string"""
    # seq = seq[len(seq) % 4:]
    seq = max(seq.split(b"\x00"), key=len)

    enc_seq = []
    for s in re.split(b'(\x81\x42|\x81\x48|\x20)', seq):
        if (len(s) >= 2):
            enc_seq.append(s[len(s) % 2:].decode("shift-jis", "ignore"))

    return("".join(enc_seq))


if __name__=="__main__":
    text = input()

    print(encode_english(text))
    # for seq in text.split(" 0 "):
        # seq = seq.replace("47", "")
        # seq = seq.replace(" ", "")
        # seq = bytes.fromhex(seq)

        # seq = seq.decode("shift-jis", "ignore")
        # print(seq)

        # seq = translator.translate(seq, lang_tgt="en")
        # print(seq)

        # seq = encode_english(seq)
        # print(seq)

        # print(decode_seq(seq))
