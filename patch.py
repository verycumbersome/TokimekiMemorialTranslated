#!/usr/bin/env python3
"""
All ROM utils for patching the translations back into the game
"""

import os
import json

import mmap

from halo import Halo
from tqdm import tqdm
from shutil import copyfile

import numpy as np
import pandas as pd

import utils
import config

path = os.path.dirname(__file__)

spinner = Halo(text='Creating blocks', spinner='dots')

# Define globals
rom_fp = os.open(os.path.join(path, config.BIN_PATH), os.O_RDWR)
mm = mmap.mmap(rom_fp, 0, prot=mmap.PROT_READ)


class Block:
    def __init__(self, table, address):
        self.table = table
        self.address = address

        # Initialize class vars
        self.seqs = []
        self.pointers = []

        # Call init functions
        self.get_pointers()
        self.get_seqs()

        if len(self.pointers) and len(self.seqs):
            self.get_offset()
            self.create_ptr_table()

    def get_pointers(self):
        tbl = self.table.replace(" ", "")

        # Make the pointer is the correct length
        if not tbl.find("80") > 6:
            return None

        # Iterate through table while appending each pointer to a list
        while tbl.find("80") > 6:
            ptr_idx = tbl.rfind("80")
            ptr_text = tbl[ptr_idx - 6:ptr_idx + 2]

            ptr = utils.read_ptr(ptr_text)
            ptr = int(ptr[2:], 16)  # Get int value of pointer

            if ptr > 0x170000 and ptr < 0x1A0000: # Make sure pointer location is sufficiently large
                self.pointers.append({
                    "hex":hex(ptr),
                    "text":ptr_text,
                    "idx":ptr,
                    # "location":hex((self.table.find(ptr_text) // 2) + self.address),
                    "location":(self.table.find(ptr_text) // 2) + self.address,
                })
            tbl = tbl[:ptr_idx - 6]

            # Replace all pointers in the table with NULL
            self.table = self.table.replace(ptr_text, "00000000")

        self.pointers = pd.DataFrame(self.pointers)

    def get_seqs(self):
        """Get sequences and indices from table in ROM"""
        self.seqs = [s.lstrip("0") for s in self.table.split("00") if len(s) > 8]
        self.seqs = [(self.table.index(s) // 2, s) for s in self.seqs]
        self.seqs = pd.DataFrame(self.seqs, columns = ["idx", "seqs"])

    def get_offset(self):
        """Find best offset to match max amount of pointers to sequences"""
        ptr_idxs = np.array(self.pointers["idx"])
        seq_idxs = np.array(self.seqs["idx"])

        self.offset = np.bincount(np.ravel(ptr_idxs[:,None] - seq_idxs[None,:])).argmax()

    def create_ptr_table(self):
        # Find address of relative pointers to seqs in the ROM
        self.seqs["addr"] = (self.seqs["idx"] + self.address).map(hex)

        # Apply best offset to the sequence indices
        self.seqs["idx"] += self.offset

        # Merge matching pointers and seqs given best offset
        self.pointers = pd.merge(self.seqs, self.pointers, on="idx")


def init_blocks():
    chunk = ""

    end = config.MEM_MAX

    blocks = []
    spinner.start()
    while True:
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)

        if table_idx < 1: # Stop parsing at end of bin file
            break

        table = mm[table_idx:end].hex()
        table = table[48:len(table) - 560] # Remove table header/footer info 

        chunk = table + chunk

        b = Block(chunk, table_idx + 24)

        if not len(b.pointers):
            end = table_idx
            continue

        overlap = len(b.pointers["hex"]) - len(np.unique(b.pointers["hex"]))

        # If theres a duplicate pointer end the chunk
        if overlap > 42:
            blocks.append(b)

            print(b.pointers)

            return(blocks)

            chunk = ""

        end = table_idx

    spinner.stop()

    return blocks


def patch(blocks):
    patched_path = "patched_rom.bin"

    copyfile(config.BIN_PATH, patched_path)

    patched_fp = os.open(os.path.join(path, patched_path), os.O_RDWR)
    patched_mm = mmap.mmap(patched_fp, 0, prot=mmap.PROT_WRITE)

    counter = 0x0000
    for b in blocks:
        for ptr in b.pointers.iterrows():
            loc = ptr[1]["location"]
            p = patched_mm[loc:loc+4].hex()
            if "80" in p:
                print(ptr)

                patched_mm.seek(loc)
                patched_mm.write(b"\x00\x00\x00\x00")

        # print(b.pointers)

    # with open("ROM.bin", "w+") as patched_rom:
        # pass




if __name__=="__main__":
    blocks = init_blocks()

    patch(blocks)

    # with open("test_table2.txt", "r") as test_table_fp:
        # chunk = test_table_fp.read()

    # blocks = {}
    # chunk = chunk.split("00FFFFFFFFFFFFFFFFFFFF00")
    # chunk = [x.replace("\n", "")[24:config.BLOCK_SIZE] for x in chunk if x]
    # chunk = "".join(chunk)

    # b = Block(chunk, 0)

    # print(b.seqs)
    # print(b.pointers)
