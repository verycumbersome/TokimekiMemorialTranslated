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

        # Make sure the block size is correct
        assert len(table) % config.BLOCK_SIZE == 0, "Incorrect block table length"

        # Initialize class vars
        self.seqs = []
        self.pointers = []
        self.num_pointers = 0
        self.num_seqs = 0

        # Call init functions
        self.get_pointers()
        self.get_seqs()

        if len(self.pointers) and len(self.seqs):
            self.get_offset()
            self.create_ptr_table()

    def get_pointers(self):
        tbl = self.table.replace(" ", "")

        # Make the pointer is the correct length
        tbl = [p[-6:] + "80" for p in self.table.split("80") if len(p) >= 6]

        # Iterate through table while appending each pointer to a list
        for ptr_text in tbl:
            ptr = int(utils.reverse_ptr(ptr_text)[2:], 16)

            if ptr > 0x190000 and ptr < 0x1A0000: # Make sure pointer location is sufficiently large
                self.pointers.append({
                    "hex": hex(ptr),
                    "text": ptr_text,
                    "idx": ptr
                })
            # Replace all pointers in the table with NULL
            self.table = self.table.replace(ptr_text, "00000000")

        self.num_pointers = len(self.pointers)
        self.pointers = pd.DataFrame(self.pointers)

    def get_seqs(self):
        #TODO FIX THE SEQUENCE EXTRACTION FROM TABLE
        """Get sequences and indices from table in ROM"""
        self.seqs = [s.lstrip("0") for s in self.table.split("00") if len(s) > 4]
        self.seqs = [s for s in self.seqs if utils.check_validity(s) > 0.7]
        self.seqs = [(self.table.index(s) // 2, s) for s in self.seqs]
        self.seqs = pd.DataFrame(self.seqs, columns = ["idx", "seqs"])
        self.num_seqs = len(self.seqs)

    def get_offset(self):
        """Find best offset to match max amount of pointers to sequences"""
        ptr_idxs = np.array(self.pointers["idx"])
        seq_idxs = np.array(self.seqs["idx"])

        self.offset = np.bincount(np.ravel(ptr_idxs[:,None] - seq_idxs[None,:])).argmax()

    def create_ptr_table(self):
        # Find address of relative pointers to seqs in the ROM
        # self.seqs["addr"] = (self.seqs["idx"] + self.address).map(hex)

        # Apply best offset to the sequence indices
        self.seqs["idx"] += self.offset

        # Merge matching pointers and seqs given best offset
        self.pointers = pd.merge(self.seqs, self.pointers, on="idx")

        # print(self.pointers)


def init_blocks():
    chunk = ""

    end = config.MEM_MAX

    blocks = []

    while True:
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)

        if table_idx < 1: # Stop parsing at end of bin file
            break

        table = mm[table_idx:end].hex()
        table = table[config.HEADER_SIZE:-config.FOOTER_SIZE] # Remove table header/footer info 

        chunk = table + chunk

        b = Block(chunk, table_idx + 24)

        print(b.num_pointers)
        print(hex(table_idx))

        if not len(b.pointers):
            end = table_idx
            continue

        # print(len(b.pointers), len(np.unique(b.pointers["hex"])))

        # If theres a duplicate pointer end the chunk
        # overlap = len(b.pointers["hex"]) - len(np.unique(b.pointers["hex"]))
        # if overlap > 42:
        # tmp = Block(table, table_idx + 24)
        # if not len(tmp.pointers):
            # b.pointers["location"] = b.pointers["text"].map(
                # lambda x: mm.find(bytes.fromhex(x), table_idx)
            # )
            # # b.pointers["addr"] = b.pointers["seqs"].map(
                # # lambda x: mm.find(bytes.fromhex(x), table_idx)
            # # )
            # blocks.append(b)

            # print(b.pointers)

            # chunk = ""
            # return blocks

        end = table_idx

    return blocks


def patch(blocks):
    patched_path = "patched_rom.bin"

    copyfile(config.BIN_PATH, patched_path)

    patched_fp = os.open(os.path.join(path, patched_path), os.O_RDWR)
    patched_mm = mmap.mmap(patched_fp, 0, prot=mmap.PROT_WRITE)

    counter = 0xffff0000

    out = {}
    for b in blocks:
        for ptr in b.pointers.iterrows():
            loc = ptr[1]["location"]
            p = patched_mm[loc:loc+4].hex()

            new_ptr = bytes.fromhex(utils.reverse_ptr(hex(counter)[2:]))

            patched_mm.seek(loc)
            patched_mm.write(new_ptr)

            seq = utils.encode_english("text goes here")
            seq.append(0)

            out[str(counter - 0xffff0000)] = seq

            counter += 1

    ptr_tbl_fp = open("pointer_table.json", "w")
    json.dump(out, ptr_tbl_fp)


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
