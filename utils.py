#!/usr/bin/env python3
"""
Basic utilities across all other modules
"""

import os
import re
import mmap
import json

import numpy as np

from typing import Any

import config

path = os.path.dirname(__file__)


def get_rom_path() -> str:
    """Gets the path of the rom to patch"""
    print("Which ROM would you like to patch?")
    rom_paths = os.listdir(os.path.join(path, "roms"))
    for i, p in enumerate(rom_paths):
        print("{}. {}".format(i, p))
    rom_path = rom_paths[int(input())]
    rom_path = os.path.join(path, "roms", rom_path)

    return rom_path


def clean_seq(seq):
    """handles the cleaning of a sequence to ensure correct shift-jis encoding"""
    seq = seq[:len(seq) - (len(seq) % 2)] # If seq is incorrect number of bytes

    return seq


def reverse_ptr(ptr: Any) -> str:
    """Reverse ps1 pointer from file. Useful for reading and writing ptrs to ROM"""
    if type(ptr) == str:
        ptr = reversed([ptr[i:i + 2] for i in range(0, len(ptr), 2)])
        ptr = "".join(list(ptr))

    if type(ptr) == bytes:
        ptr = reversed([ptr[i:i + 1] for i in range(0, len(ptr), 1)])
        ptr = b"".join(list(ptr))

    return ptr


def handle_dup(seq: str) -> str:
    """Takes string sequence and checks for duplicates"""
    dup = seq.split(b" ")
    dup = sum([dup[c] == dup[(c+1)%len(dup)] for c in range(len(dup))])

    if dup > 10:
        seq = b"".join(seq.split(b" ")[::2])

    return seq


def encode_english(seq: str) -> list:
    """encodes an english sequence into equivilant english shift-jis chars"""
    enc = []
    out = []
    offset = 0
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

        # Handle invalid characters
        try:
            c = bytes.fromhex(c).decode("shift-jis", "ignore")
        except ValueError:
            pass

        out += c

    # out = "".join(out)
    # print(out)

    return enc

def get_seq_offset(seq):
    """Finds the most probably starting character for a dialog sequence"""
    offset = 0
    jis_chars = 0
    for off in range(4):
        tmp = seq[off:]
        valid_chars = 0
        for c in [tmp[i:i+4] for i in range(0, len(tmp), 4)]:
            enc_char = int(c, 16)
            if 0x829E < enc_char < 0x839E: # Kana character
                valid_chars += 1
        if valid_chars > jis_chars: # Finds the best offset to align the sequence character search correctly
            offset = off
            jis_chars = valid_chars
    seq = seq[offset:]

    return seq, jis_chars


#TODO Setup nagisa to validate japanese words
def check_validity(seq: Any) -> bool:
    """Returns true if a sequence is valid given a set of criteria"""
    if len(seq) > 80 or len(seq) < 4:
        return False

    if type(seq) == bytes:
        seq = seq.hex().replace("00", "")

    # Check percentage of plausible dialog characters in seq
    seq, jis_chars = get_seq_offset(seq)

    # Conditions for being valid sequence for pointer to point to
    if jis_chars < 8:
        return False
    if any(x in seq for x in ["8142", "8148", "8149"]):
        jis_chars += 10
    if not len(seq):
        return False
    if (jis_chars / (len(seq) * 0.25) <= 0.6): # Not enough valid chars
        return False
    if "80" in seq: # Has a pointer
        return False

    return True


def decode_seq(seq: bytes) -> str:
    """Encodes hex string into shift-jis ascii string"""
    # seq = seq[len(seq) % 4:]
    # seq = max(seq.split(b"\x00"), key=len)

    out = (seq.decode("shift-jis", "ignore"))
    # enc_seq = []
    # for s in re.split(b'(\x81\x42|\x81\x48)', seq):
        # if len(s) >= 2:
            # enc_seq.append(s[len(s) % 4:].decode("shift-jis", "ignore"))

    # out = "".join(enc_seq)
    # out = out.strip()

    return out


def get_num_seqs() -> int:
    """Returns the number of japanese sequences in the game"""

    rom_fp = os.open(os.path.join(path, config.BIN_PATH), os.O_RDWR)
    mm = mmap.mmap(rom_fp, 0, prot=mmap.PROT_READ)

    end = 0
    while True:
        idx = mm.rfind(b"\x00", 0, end)

        print(idx)

        end = idx


if __name__=="__main__":
    get_rom_path()
    # text = input()
    # seq = "This is a longer sentence but the text is fucked"

    # fp = open("pointer_table.json", "w")
    # seq = encode_english(seq)

    # out = {
        # "0":seq
    # }

    # json.dump(
        # out,
        # fp
    # )
