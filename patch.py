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
    def __init__(self, tid, table, address, block_num):
        self.tid = tid
        self.table = table
        self.address = address
        self.block_num = block_num

        if len(table) != config.BLOCK_SIZE:
            print("Incorrect block table length", len(table))
            print("Block table length should be", config.BLOCK_SIZE)

        # Graph
        self.connected = []

        # Initialize class vars
        self.seqs = []
        self.offsets = []
        self.pointers = []
        self.is_empty = True

        # Call init functions
        self.get_table_pointers()

        if len(self.pointers) > 40:
            self.get_seqs()
            self.get_offset()
            self.is_empty = False

        # if len(self.seqs):
            # self.create_ptr_table()
            # self.is_empty = False

        self.pointers = pd.DataFrame(self.pointers)


    def __str__(self):
        out = "Block ID:" + self.tid + "----------------\n"
        out += "Block Addr: " + hex(self.address) + "------------------"

        return out


    def get_table_pointers(self):
        tbl = self.table.replace(" ", "")

        # Make the pointer is the correct length
        if not tbl.find("80") > 6:
            return None

        # Iterate through table and pop the pointer from the end of the table
        # while appending each pointer to a list
        while tbl.find("80") > 6:
            ptr_idx = tbl.rfind("80")
            ptr = utils.read_ptr(tbl[ptr_idx - 6:ptr_idx + 2])
            ptr = int(ptr[2:], 16)  # Convert pointer to int

            if ptr > 0x100000: # Make sure pointer location is sufficiently large
                self.pointers.append({
                    "hex":hex(ptr),
                    "text":tbl[ptr_idx - 6:ptr_idx + 2],
                    "idx":ptr
                })
            tbl = tbl[:ptr_idx - 6]


    def get_seqs(self):
        # Checks to make sure that the sequence is a valid shift-jis sentence
        for s in self.table.split("00"):
            try:
                seq = utils.decode_seq(bytes.fromhex(s))
                if utils.check_validity(seq) > 0.7 and len(seq) > 1:
                    self.seqs.append(s)
            except:
                pass


    def get_offset(self):
        # Get sentence indices and sort 
        self.seqs = [(self.table.index(s), s) for s in self.seqs]
        self.seqs = pd.DataFrame(self.seqs, columns = ["idx", "seqs"])
        self.seqs = self.seqs.sort_values("idx")

        # Get pointers and sort by relative pointer pos in table
        self.pointers = sorted(self.pointers, key=lambda x: x["idx"])
        self.pointers = pd.DataFrame(self.pointers)


        # Find best offset to match max amount of pointers to sequences 
        ptr_idxs = np.array(self.pointers["idx"])
        seq_idxs = np.array(self.seqs["idx"])

        if ptr_idxs.size == 0 or seq_idxs.size == 0:
            return

        for p in ptr_idxs:
            offset = p - seq_idxs[0]

            offset_idxs = ptr_idxs - offset
            matches = np.intersect1d(offset_idxs, seq_idxs)

            self.offsets.append(offset)


    # def create_ptr_table(self):
        # for i, p in enumerate(self.pointers):
            # p["addr"] = hex(self.address + p["idx"]) # Address in ROM that pointer points to given offset

            # if p["idx"] >= 0 and p["idx"] < len(self.table):
                # for s in self.seqs.itertuples():
                    # s = tuple(s)
                    # if s[1] == p["idx"]:
                        # p["offset"] = s[1] + self.address
                        # p["seq"] = s[2]
                        # p["decoded"] = bytes.fromhex(s[2]).decode("shift-jis", "ignore")

                # self.pointers[i] = p


    def match_block(self, block):
        """Checks all possible block offsets with another block's offsets"""

        # print(self)
        # print(block)

        for offsets in [block.offsets, self.offsets]:
            best = 0

            for offset in offsets:
                b1_matches = self.pointers["idx"] - offset
                b1_matches = np.intersect1d(self.seqs["idx"], b1_matches)

                b2_matches = block.pointers["idx"] - offset
                b2_matches = np.intersect1d(block.seqs["idx"], b2_matches)

                matches = (len(b1_matches) + len(b2_matches))

                if matches > best:
                    best = matches

                    # print(offset)
                    # print("Block1 matches: ", len(b1_matches))
                    # print("Block2 matches: ", len(b2_matches))
                    # print()

        return best


def init_blocks():
    """ Get all pointers from a 'block' in ROM

    Args:
        bin_path: Path for game bin file

    Returns:
        Returns dict of pointer tables with associated data

    """

    # blocks = {}
    blocks = []
    end = config.MEM_MAX

    # spinner.start()
    while True:
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)

        if table_idx < 1: # Stop parsing at end of bin file
            break

        table = mm[table_idx:end].hex()

        tid = table[24:32] # Get id
        table = table[48:len(table) - 560] # Remove table header/footer info 

        b = Block(tid, table, table_idx + 48, len(blocks))

        if not b.is_empty:
            blocks.append(b)

        end = table_idx

    # spinner.stop()

    return blocks


def solve_blocks(blocks):
    graph = []

    # for b1 in tqdm(range(len(blocks)), desc="solving blocks"):
    for b1 in range(len(blocks)):
        best = 0
        best_match = None

        # for b2 in tqdm(range(b1 + 1, len(blocks)), desc="block", leave = False):
        for b2 in range(b1 + 1, len(blocks)):
            match = blocks[b1].match_block(blocks[b2])
            print(match)

            if match > best:
                best = match
                best_match = (b1, b2)

        graph.append(best_match)

    print(graph)


if __name__=="__main__":
    blocks = init_blocks()[:20]

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

    solve_blocks(blocks)




