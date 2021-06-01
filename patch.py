#!/usr/bin/env python3
"""
All ROM utils for patching the translations back into the game
"""

import os
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
        self.chunk = table
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

    def get_table_pointers(self):

        print(self.table)
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
        # Get sentence indices
        self.seqs = [s.lstrip("0") for s in self.table.split("00") if len(s) > 8]
        self.seqs = [(self.table.index(s), s) for s in self.seqs]
        self.seqs = pd.DataFrame(self.seqs, columns = ["idx", "seqs"])

    def get_offset(self):
        self.pointers = self.pointers.sort_values("idx")
        self.seqs = self.seqs.sort_values("idx")

        # Find best offset to match max amount of pointers to sequences
        ptr_idxs = np.array(self.pointers["idx"])
        seq_idxs = np.array(self.seqs["idx"])

        matches = np.ravel(ptr_idxs[:,None] - seq_idxs[None,:])
        self.offset = np.bincount(matches).argmax()

:   def create_ptr_table(self):
        self.seqs["idx"] += self.offset
        self.pointers["addr"] = self.pointers["idx"] + self.address

        # Merge matching pointers and seqs given best offset
        # self.pointers = pd.merge(self.pointers, self.seqs, on="idx")
        self.pointers = pd.merge_asof(self.pointers, self.seqs,
                                      on="idx", tolerance = 20, direction = "nearest")

        self.pointers = self.pointers.dropna()

        print(self.pointers)
        print(len(self.pointers))


def init_blocks():
    chunk = ""

    blocks = []
    end = config.MEM_MAX

    counter = 0
    while True:
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)

        if table_idx < 1: # Stop parsing at end of bin file
            break

        table = mm[table_idx:end].hex()
        table = table[48:len(table) - 560] # Remove table header/footer info 

        chunk = table + chunk

        b = Block(chunk, table_idx + 24, len(blocks))

        print(b.pointers)

        if b.pointers.empty:
            end = table_idx
            continue

        # # If theres a duplicate pointer end the chunk
        if len(np.unique(b.pointers["hex"])) != len(b.pointers["hex"]):
            b = Block(chunk[config.BLOCK_SIZE:], table_idx + config.BLOCK_SIZE + 48, len(blocks))
            blocks.append(b)

            for p in b.pointers.itertuples():
                print(tuple(p))

            # exit()
            chunk = ""

        end = table_idx

    return blocks



if __name__=="__main__":
    # blocks = init_blocks()

    with open("test_table2.txt", "r") as test_table_fp:
        chunk = test_table_fp.read()

    # blocks = {}
    # chunk = chunk.split("00FFFFFFFFFFFFFFFFFFFF00")
    # chunk = [x.replace("\n", "")[24:config.BLOCK_SIZE] for x in chunk if x]
    # chunk = "".join(chunk)

    # print(chunk)

    b = Block(chunk, 0, 0)

    # print(b.seqs)
    # print(b.pointers)
