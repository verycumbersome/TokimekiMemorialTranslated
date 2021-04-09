#!/usr/bin/env python3
import os
import re
import sys
import json
import time

import tqdm
import mmap
import hashlib

from transformers import pipeline
from google_trans_new import google_translator

import utils
import config

path = os.path.dirname(__file__)

def read_ptr(ptr):
    """Read ps1 pointer from file"""
    ptr = reversed([ptr[i:i + 2] for i in range(0, len(ptr), 2)])
    ptr = "".join(list(ptr))

    return ptr


def read_ptr_table(seq):
    """Read ps1 pointer table from file"""
    seq = [x + "80" for x in seq.replace(" ", "").split("80")[0::2]]

    for ptr in seq:
        ptr = read_ptr(ptr)

        print(ptr)

    # print(seq)


def parse_shift_table(filename):
    """Quick util to generate shift-jis atlas table"""
    shift_table = open(os.path.join(path, filename), "r")

    with open(os.path.join(path, "patch/game.tbl"), "w") as table:
        table.write(config.TABLE_HEADER)
        for line in tqdm.tqdm(shift_table.readlines()):
            line = line.split("#")[0].split("\t")[:2]

            left = str(line[0][2:])
            right = bytes.fromhex(left).decode("shift-jis", "ignore")

            if left and right and not any(re.findall("<|>", right, re.IGNORECASE)):
                table.writelines(left + "=" + right + "\n")


def create_atlas(bin_path, dialog_path, trans_path):
    """Create Atlas file for referencing dialog translations in ROM"""
    f_ptr = os.open(os.path.join(path, bin_path), os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)
    write_ptr = 0x29D3E3BE

    dialog_table = json.load(open(os.path.join(path, dialog_path), "r"))
    translation_table = json.load(open(os.path.join(path, trans_path), "r"))

    with open(os.path.join(path, "patch/Atlas.txt"), "w") as atlas_file:
        atlas_file.write(config.ATLAS_HEADER)

        for item in tqdm.tqdm(dialog_table):
            seq = dialog_table[item]["seq"]
            addr = dialog_table[item]["addr"]
            seq_size = sys.getsizeof(seq)

            if int(addr[2:], 16) < 0x08F510:
                continue

            # mm.seek(write_ptr)
            # mm.write(utils.encode_english("asdf"))
            write_ptr += seq_size

            print(addr[2:])
            print(hex(write_ptr)[2:])
            line_buf = f"#JMP(${addr[2:]}) // Jump to insertion point\n"
            line_buf += f"#WRITE(ptr, ${hex(write_ptr)[2:]})\n"
            # line_buf += f"{seq}\n\n"
            line_buf += "ｗｈａｔ　ｓｈｏｕｌｄ[end]\n\n"
            atlas_file.writelines(line_buf)


if __name__=="__main__":
    # parse_shift_table(os.path.join(path, "patch/shiftjis_table.txt"))

    # read_ptr_table(input())

    create_atlas(
        os.path.join(path, "patch/Atlas.bin"),
        os.path.join(path, "patch/dialog_table.json"),
        os.path.join(path, "patch/translation_table.json"),
    )
