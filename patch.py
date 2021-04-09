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
shiftjis_table = None


def read_ptr(ptr):
    """Read ps1 pointer from file"""
    ptr = reversed([ptr[i:i + 2] for i in range(0, len(ptr), 2)])
    ptr = "".join(list(ptr))

    return ptr


def get_ptr_tables(bin_path):
    """ Get all pointers from table with associated data

    Args:
        bin_path: Path for game bin file

    Returns:
        Returns dict of pointer tables with associated data

    """

    f_ptr = os.open(os.path.join(path, bin_path), os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    tables = {}
    end = config.MEM_MAX

    while (True):
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)
        if (table_idx < 1):
            break

        table = mm[table_idx:end][len(config.TABLE_SEP):].hex()
        tid = table[:8]
        table = table[8:].lstrip()

        addr = get_tbl_addrs(table, table_idx + 0x18)
        if addr:
            tables[tid] = addr

        end = table_idx


    print(json.dumps(tables, indent=4))
    # print(len(tables))


def get_tbl_addrs(tbl, rom_start):
    """Read a pointer table and return relative ROM and RAM address for each pointer

    Args:
        tbl: Input pointer table to parse
        rom_start: Start address for tbl position in ROM

    Returns:
        Returns dict of relative pointer addresses

    """

    if not tbl.find("80") > 6:
        return None

    out = {}
    tbl = tbl.replace(" ", "")
    ram_start = int(read_ptr(tbl[tbl.find("80") - 6:tbl.find("80") + 2])[2:], 16)

    while (tbl.find("80") > 6):
        ptr_idx = tbl.rfind("80")
        ptr = read_ptr(tbl[ptr_idx - 6:ptr_idx + 2])

        ptr = int(ptr[2:], 16)

        offset = ptr - ram_start
        out[hex(offset + rom_start)] = hex(ptr)

        tbl = tbl[:ptr_idx - 6]

    return out


def create_shiftjis_table(filename, create_atlas=False):
    """Quick util to generate shift-jis atlas table

    Args:
        filename: Filename for the shift-jis translation rules
        create_atlas: Boolean for whether to create atlas shift-jis table

    Returns:
        Returns encoding table for shift-jis as a dict

    """

    print(shiftjis_table)
    shift_table = open(os.path.join(path, filename), "r")

    tbl = {}
    for line in tqdm.tqdm(shift_table.readlines()):
        line = line.split("#")[0].split("\t")[:2]

        left = str(line[0][2:])
        right = bytes.fromhex(left).decode("shift-jis", "ignore")

        if left and right and not any(re.findall("<|>", right, re.IGNORECASE)):
            tbl[left] = right

    if create_atlas:
        with open(os.path.join(path, "patch/Atlas.tbl"), "w") as table:
            table.write(config.TABLE_HEADER)

            for item in tbl:
                table.writelines(item + "=" + tbl[item] + "\n")

    return tbl


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
    get_ptr_tables(config.TOKIMEKI_PATH)
    # shiftjis_table = create_shiftjis_table(os.path.join(path, "patch/shiftjis_table.txt"))

    # with open("test_table.txt", "r") as test_table_fp:
        # get_tbl_addrs(test_table_fp.read(), 0x19C804, 0x6481998)

    # create_atlas(
        # os.path.join(path, "patch/Atlas.bin"),
        # os.path.join(path, "patch/dialog_table.json"),
        # os.path.join(path, "patch/translation_table.json"),
