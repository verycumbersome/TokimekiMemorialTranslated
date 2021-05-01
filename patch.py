#!/usr/bin/env python3
import os
import re
import sys
import json
import time

import tqdm
import mmap
import hashlib
import numpy as np

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
    """ Get all pointers from a 'block' in ROM

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
        table = table[0x18:]

        addr = get_tbl_addrs(table)
        if addr:
            tables[tid] = addr

        end = table_idx


    # for tid in tables:
        # for ptr in tables[tid]:
            # if "0x6481" in ptr:
                # print(tables[tid][ptr])
                # print("asdf")

    # print(json.dumps(tables, indent=4))
    # print(len(tables))


def get_tbl_addrs(table):
    """Read a pointer table and return relative ROM and RAM address for each pointer

    Args:
        tbl: Input pointer table to parse
        rom_start: Start address for tbl position in ROM

    Returns:
        Returns dict of relative pointer addresses

    """

    pointers = []
    sentences = []

    # Get all table pointers in table
    if not table.find("80") > 6:
        return None

    tbl = table.replace(" ", "")
    while (tbl.find("80") > 6):
        ptr_idx = tbl.rfind("80")
        ptr = read_ptr(tbl[ptr_idx - 6:ptr_idx + 2])
        ptr = int(ptr[2:], 16)

        if ptr > 0x100000:
            pointers.append({
                "hex":hex(ptr),
                "text":tbl[ptr_idx - 6:ptr_idx + 2],
                "val":ptr
            })
        tbl = tbl[:ptr_idx - 6]

    for p in pointers:
        tbl = table.replace(p["text"], "00")

    # Get the sentences from table
    # TODO Fix this bytes fromhex bullshit
    for sentence in tbl.split("00"):
        try:
            seq = utils.decode_seq(bytes.fromhex(sentence))
            if (utils.check_validity(seq) > 0.7):
                sentences.append(sentence)
        except:
            pass

    # Get sentence indices
    sens = sorted([table.index(s) for s in sentences])
    pointers = sorted(pointers, key=lambda x: x["val"])

    best = []
    for ptr in pointers:
        offset = ptr["val"] - sens[0] if sens else 0
        ptrs = [p["val"] - offset for p in pointers]

        matches = [p in sens for p in ptrs]
        best.append({"offset":offset, "matches":matches})

    if len(best) > 1:
        best = max(best, key = lambda x: sum(x["matches"]))
        pointers = [p["val"] - best["offset"] for p in pointers]

        print(sens)
        # print(pointers)

    # print(pointers)
    # print(hex(best["offset"]))
    # print(sum(best["matches"]))



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

tbl = "82c18149204782c182c48141208cc38eae82e482a982e882b382f1814800000082bb82a4814182c582b782af82ea82c782e081638142209053939682bd82e882cd81412082b282b482a282dc82b782a98148000082cd82a0816381482082c882f182c582b582e582a481480089b482aa81414782cc8370815b83678369815b81422096bc914f82cd814146814200000082bb82ea82cd81418eb897e782f082a282bd82b582dc82b582bd81422082bb82ea82c582cd81418da193fa82cd2082e682eb82b582ad82a88ae882a282a282bd82b582dc82b781420000000082b182bf82e782b182bb81420000000024c7198040c7198098c71980acc71980fcc7198020c81980acee198054c819806cc8198090c81980dcc8198034c5198040c5198054c5198078c61980d0c619801cc71980ecc81980060100ff07ff000001ff00000001000100010001ff00000000ff00000001ff000001000100010001000100ff34c9198038c919803cc9198040c919804cc9198050c9198054c919800000000000000000000000000000000000000000000000000000000009000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000e000002000000000000000000000000000000000000000000000000000000000000000000000000000000000f0000001d000003000000000000000000000000000000000000000000000000000000000000000000000000000000001e0000003000000400000000000000000000000000000000000000000000000000000000000000000000000000000000310000004700000500000000000000000000000000000000000000000000000000000000000000000000000000000000480000005f0000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001030000010000000000000000000000000000000000000000000000000000000000000000000000000000000060000000810000070000000000000000000000000000000000000000000000000000000000000000000000000000000082000000a500000800000000000000000000000000000000000000000000000000000000000000000000000000000000a6000000bb00000900000000000000000000000000000000000000000000000000000000000000000000000000000000bc000000c500000a00000000000000000000000000000000000000000000000000000000000000000000000000000000c6000000e000000b000000000000000000000000000000000000000000000000000000000000000000000000000000007cc9198094c91980acc91980c4c91980dcc91980f4c919800cca198024ca19803cca198054ca19806cca198084ca19809cca1980b4ca1980ccca1980e4ca1980fcca198014cb19802ccb198044cb19805ccb198074cb19808ccb1980a4cb1980bccb1980d4cb1980eccb198004cc198010cc198014cc198018cc198038cc19803ccc198044cc198082888285828c828c828f2082948289828d816992a9918182ad919682e982cc82cd8141208b438e9d82bf82aa82a282a282c882a08142816a000000008ccc198082a882cd82e682a481420000cccc1980816381492082a8814182a882cd82e682a4814220816993e982ea93e982ea82b582a2937a82be82c882a08142816a00008c4e82e08da18141919682c182c482ab82bd82cc8148000082a082a0814182bb82a482be82e68142208c4e82e082bb82a482c882cc8148008e848141968892a98254824f834c838d82cc20838d815b8368838f815b834e82f0208c8782a982b582bd82b182c682c882a282a982e781420000000082dc8141968892a981418254824f834c838d8149208c4e8163814182ab82e782df82ab8d828d5a82cc906c814800000082a482f1814182bb82a48142208e84814190b490ec965d8142208c4e82e082bb82a482c882cc81480000000082bb82a4814189b481414681422090b490ec82c182c4816381422082a082cc81419085896a959482cc90b490ec82b382f181480082bb82a482be82af82c7816381422082d682a581638142208e8482cc8e968141926d82c182c482e982f182be81420000926d82c182c482e982e089bd82e081412092b4974c96bc906c82b682e182c882a282a9814200000092b48d828d5a8b8982cc8f9783588343837d815b82be82e681422082e082c182c6814196b38d9c82c896ba82be82c6208e7682c182c482bd82af82c7816381420000000092b448454c4c4f48454c4c4f48454c4c4f48454c4c4f48454c4c4f48454c4c4f48454c4c4f48454c4c4f00000000000000000000dccc19800ccd198024cd198044cd198080cd1980b0cd1980dccd198010ce198040ce198068ce1980acce198082cd82cd82cd816381422090b490ec82b382f182cc91ab8ee882dc82c682a282c92082c882e782c882ab82e182a282a282af82c782cb81420000000082cd82cd82cd82cd814182c882e782c882a282c182c481422082b682e182a08e84814182e082a482d082c682c1919682e82082b582c482ad82e982a982e781420000000089b482cd814182e082a48fad82b58b7882f182c582a282ad82e681420000000082b182cc83578385815b8358814120975d82c182bd82a982e782a082b082e981422082b682e182a0814200000ccf198048cf19808ccf1980accf1980816381422082f182ae82f182ae82f182ae816381422083760cced378a2276e0404a31c9aff40bd7d393b60736dcd99e33271bb7d7149babe657c8c2c78c2d134bdcd1b175d5ec0a738b2196244adf34333957cdddae4a5c2ed473348ff007a3c1835c46759d0be37dfdf9efbab0977aa0a476b537ba1327a01c2fe7f270bedcdc6fe57f12784c139fac4df37c0b42c564c0942db8ffff30939c73026858c7d5b6f58dd0f4e01e25a5a0f3f5e535be2ea671aa09fd4264c47731a4084b0ae938354c1add243aa6ba07bcbdc0ec2ba488283aa1f344e2f4076f2832f6328694bed3f73843c12cc58f8bf166a08ffc8489ab7b5e1c17d82642c9feb42581da5934dd55372c9bb2ed82828f246fe9295cc5a2eede6535b0b46d4d91aae80bd275e3e113f056706bce980103fc57c7aae6fdc"

if __name__=="__main__":
    get_ptr_tables(os.path.join(path, "patch/Atlas.bin"))
    # get_tbl_addrs(tbl)
    # shiftjis_table = create_shiftjis_table(os.path.join(path, "patch/shiftjis_table.txt"))

    # with open("test_table.txt", "r") as test_table_fp:
        # get_tbl_addrs(test_table_fp.read(), 0x19C804, 0x6481998)

    # create_atlas(
        # os.path.join(path, "patch/Atlas.bin"),
        # os.path.join(path, "patch/dialog_table.json"),
        # os.path.join(path, "patch/translation_table.json"),
        # )
