#!/usr/bin/env python3
"""
All ROM utils for patching the translations back into the game
"""

import os
import re
import sys
import json


import mmap

from halo import Halo
from tqdm import tqdm

import numpy as np
import pandas as pd

import utils
import config

path = os.path.dirname(__file__)

spinner = Halo(text='Creating blocks', spinner='dots')

# Define globals
f_ptr = os.open(os.path.join(path, config.BIN_PATH), os.O_RDWR)
mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)


class Block:
    def __init__(self, table, address, block_num):
        self.table = table
        self.address = address
        self.block_num = block_num

        # Make sure the block size is correct
        # assert len(table) % config.BLOCK_SIZE == 0, "Incorrect block table length"

        # Initialize class vars
        self.seqs = []
        self.offsets = []
        self.pointers = []
        self.is_empty = True

        # Call init functions
        self.get_table_pointers()
        self.pointers = pd.DataFrame(self.pointers)

        if len(self.pointers) > 10:
            self.get_seqs()
            self.get_offset()

            self.validity = len(self.pointers) / (len(self.offsets) + 0.0001)

        if len(self.seqs):
            self.create_ptr_table()
            self.is_empty = False


    def __str__(self):
        out = "Block ID:" + self.tid + "----------------\n"
        out += "Block Addr: " + hex(self.address) + "------------------"

        return out


    def get_table_pointers(self):
        tbl = self.table.replace(" ", "")

        # Make the pointer is the correct length
        if not tbl.find("80") > 6:
            return None

        # Iterate through table while appending each pointer to a list
        while tbl.find("80") > 6:
            ptr_idx = tbl.rfind("80")
            ptr = utils.read_ptr(tbl[ptr_idx - 6:ptr_idx + 2])
            ptr = int(ptr[2:], 16)  # Convert pointer to int
            ptr_text = tbl[ptr_idx - 6:ptr_idx + 2]

            # Replace all pointers in the table with NULL
            self.table = self.table.replace(ptr_text, "00000000")

            if ptr > 0x170000 and ptr < 0x1A0000: # Make sure pointer location is sufficiently large
                self.pointers.append({
                    "hex":hex(ptr),
                    "text":ptr_text,
                    "idx":ptr
                })
            tbl = tbl[:ptr_idx - 6]


    def get_seqs(self):
        # Checks to make sure that the sequence is a valid shift-jis sentence
        table = [x.lstrip("0") for x in self.table.split("00") if len(x) > 4]

        for s in table:
            s = utils.clean_seq(s)

            seq = utils.decode_seq(bytes.fromhex(s))
            if utils.check_validity(seq) > 0.7 and len(seq) > 1:
                self.seqs.append(s)

        # print(self.seqs)


    def get_offset(self):
        # Get sentence indices and sort 
        self.seqs = [(self.table.index(s), s) for s in self.seqs]
        self.seqs = pd.DataFrame(self.seqs, columns = ["idx", "seqs"])
        self.seqs = self.seqs.sort_values("idx")

        print(self.seqs)

        # Get pointers and sort by relative pointer pos in table
        self.pointers = self.pointers.sort_values("idx")

        # Find best offset to match max amount of pointers to sequences 
        ptr_idxs = np.array(self.pointers["idx"])
        seq_idxs = np.array(self.seqs["idx"])

        self.best = np.bincount(np.ravel(ptr_idxs[:,None] - seq_idxs[None,:])).argmax()
        l = len(np.intersect1d(ptr_idxs, (seq_idxs + self.best)))


    def create_ptr_table(self):
        self.pointers["idx"] -= self.best
        self.pointers["addr"] = list(map(hex, self.pointers["idx"] + self.address))
        self.pointers["addr"] = np.array(self.pointers["addr"])

        # Merge matching pointers and seqs given best offset
        # self.pointers = pd.merge(self.pointers, self.seqs, on="idx", how="left")
        self.pointers = pd.merge(self.pointers, self.seqs, on="idx")

        print(self.pointers)


def init_blocks():
    # x = "82 E0 8D A1 81 41 91 96 82 C1 82 C4 82 AB 82 BD 82 CC 81 48 00 00 82 A0 82 A0 81 41 82 BB 82 A4 82 BE 82 E6 81 42 20 8C 4E 82 E0 82 BB 82 A4 82 C8 82 CC 81 48 00 8E 84 81 41 96 88 92 A9 82 54 82 4F 83 4C 83 8D 82 CC 20 83 8D 81 5B 83 68 83 8F 81 5B 83 4E 82 F0 20 8C 87 82 A9 82 B5 82 BD 82 B1 82 C6 82 C8 82 A2 82 A9 82 E7 81 42 00 00 00 00 82 DC 81 41 96 88 92 A9 81 41 82 54 82 4F 83 4C 83 8D 81 49 20 8C 4E 81 63 81 41 82 AB 82 E7 82 DF 82 AB 8D 82 8D 5A 82 CC 90 6C 81 48 00 00 00 82 A4 82 F1 81 41 82 BB 82 A4 81 42 20 8E 84 81 41 90 B4 90 EC 96 5D 81 42 20 8C 4E 82 E0 82 BB 82 A4 82 C8 82 CC 81 48".replace(" ", "").lower()

    chunk = ""

    blocks = []
    end = config.MEM_MAX

    # spinner.start()
    while True:
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)

        if table_idx < 1: # Stop parsing at end of bin file
            # spinner.stop()
            break

        table = mm[table_idx:end].hex()
        table = table[48:len(table) - 560] # Remove table header/footer info 

        chunk = table + chunk

        b = Block(chunk, table_idx + 24, len(blocks))

        if b.pointers.empty:
            end = table_idx
            continue

        # if x in chunk:
            # print(chunk)

        if len(np.unique(b.pointers["hex"])) != len(b.pointers["hex"]): # If theres a duplicate pointer
            b = Block(chunk[config.BLOCK_SIZE:], table_idx + config.BLOCK_SIZE + 48, len(blocks))
            blocks.append(b)

            # if not b.is_empty:
                # print(b.pointers)
                # print("Block validity", b.validity)
                # print()

            exit()
            chunk = ""

        end = table_idx

    return blocks



if __name__=="__main__":
    blocks = init_blocks()

    # with open("test_table.txt", "r") as test_table_fp:
        # chunk = test_table_fp.read()

    # blocks = {}
    # chunk = chunk.split("00FFFFFFFFFFFFFFFFFFFF00")
    # chunk = [x.replace("\n", "")[:config.BLOCK_SIZE] for x in chunk if x]

    # for index, tbl in enumerate(chunk):
        # tid = tbl[:8]
        # b = Block(tid, tbl, index * 4096, 1)

        # blocks[index] = b


        # if index > 2:
            # break
