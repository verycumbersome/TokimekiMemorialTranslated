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
import matplotlib.pyplot as plt

import utils
import config
import translation

# Globals
path = os.path.dirname(__file__)


class Block:
    """A block in memory from the ROM separated by the PS1 pointer separator"""

    def __init__(self, table, address):
        self.table = table
        self.address = address

        # Assert correct PS1 block size(4096 bits)
        assert len(table) % config.BLOCK_SIZE == 0, "Incorrect block table length" + str(len(table))

        # Initialize class vars
        self.seqs = []
        self.pointers = []

        # Call init functions
        self.get_pointers()
        self.get_seqs()
        self.create_ptr_table()

    def __repr__(self):
        print("[---------------------------------------------------------------------------]")
        print("[---------------------------------------------------------------------------]")
        print("[---------------------------------NEW BLOCK---------------------------------]")
        print("[---------------------------------------------------------------------------]")
        print("[---------------------------------------------------------------------------]")
        print("Address: {}".format(hex(self.address)))
        print("Num Seqs: {}".format(len(self.seqs)))
        print("Num Pointers: {}".format(len(self.pointers)))
        print("Pointers: ")
        print(self.pointers)
        print("Sequences: ")
        print(self.seqs)

        return("\n")

    def get_pointers(self):
        """Get a list of all pointers in a block within a given range"""


        # Extract all potential pointers from table
        tbl = self.table.replace("00", "")
        tbl = [p[-6:] + "80" for p in tbl.split("80") if len(p) >= 4]

        # Iterate through table and append each pointer to a list
        for ptr_text in tbl:
            ptr = int(utils.reverse_ptr(ptr_text)[2:], 16)
            try:
                ptr_location = self.table.index(ptr_text) // 2 + self.address
            except:
                continue

            # if ptr > 0x195000 and ptr < 0x19FFFF:  # Make sure pointer location is correct range
            if ptr > 0x100000:  # Make sure pointer location is correct range
                self.pointers.append({
                    "hex": hex(ptr),
                    "text": ptr_text,
                    "idx": ptr,
                    "ptr_location": hex(ptr_location)
                })

        # Remove all pointers from table
        for ptr_text in tbl:
            self.table = self.table.replace(ptr_text, "00000000")

        self.pointers = pd.DataFrame(self.pointers)
        self.pointers = self.pointers.drop_duplicates(subset=["hex"])

    def get_seqs(self):
        """Get sequences and indices from table in ROM"""

        # print(utils.check_validity("82bb82ea82b682e18142"))
        # exit()

        self.seqs = []
        for seq in self.table.split("00"):
            seq = seq.replace("00", "")

            # print(seq)

            if utils.check_validity(seq):
                # print(self.table.index(seq))
                self.seqs.append((self.table.index(seq) // 2, seq))

        # print(self.table)
        # print(self.seqs)
        # exit()
        self.seqs = pd.DataFrame(self.seqs, columns=["idx", "seqs"])
        self.seqs = self.seqs.drop_duplicates(subset=["idx"])
        self.seqs["seq_location"] = ((self.seqs["idx"] * 2) + self.address).apply(hex)

    def create_ptr_table(self):
        """Find best offset to match max amount of pointers to sequences"""

        if not (len(self.pointers) and len(self.seqs)):
            return

        ptr_idxs = np.array(self.pointers["idx"])
        seq_idxs = np.array(self.seqs["idx"])

        # Find optimal offset to match most amount of pointers to seqs
        offset = np.bincount(np.ravel(ptr_idxs[:, None] - seq_idxs[None, :]))
        offset = offset.argmax()

        # Apply best offset to the sequence indices and merge given offset
        self.seqs["idx"] += offset
        self.pointers = pd.merge(self.seqs, self.pointers, on="idx")

from itertools import groupby
def group_pointers(filename):
    """Returns a translation table from a bin file"""
    out = []

    f_ptr = os.open(filename, os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    # start = 0
    # end = len(mm)

    counter = 0
    valid_ranges = []
    start = config.MEM_MIN
    end = config.MEM_MAX
    while True:
        table_idx = mm.find(config.TABLE_SEP, start, end)
        curr = mm.find(config.TABLE_SEP, table_idx+config.BLOCK_SIZE, end)

        table = mm[table_idx:curr]
        table = table[config.HEADER_SIZE:-config.FOOTER_SIZE]  # Remove table header/footer info

        try:
            block = Block(table.hex(), table_idx + 24)
            # block_value = len(block.pointers) + (len(block.seqs) * 10)
            block_value = len(block.seqs)
            counter += block_value
            print(counter)
            out.append(block_value)
        except:
            break

        if counter > 10:
            valid_range = table_idx // config.TOTAL_BLOCK_SIZE
            valid_ranges.append(valid_range)

        if counter > 0:
            counter -= 1

        # print(hex(table_idx))
        # print(block_value)
        # print()

        if table_idx < 0:
            break

        start = curr

    # print(valid_ranges)
    gb = groupby(enumerate(valid_ranges), key=lambda x: x[0] - x[1])
    # all_groups = ([i[1] for i in g] for _, g in gb)
    all_groups = ([i[1] * 4096 for i in g] for _, g in gb)
    valid_ranges = list(filter(lambda x: len(x) > 1, all_groups))

    # valid_ranges = np.array([(x[0], x[-1]) for x in valid_ranges])

    for r in valid_ranges:
        plt.axvspan(r[0], r[-1], color='red', alpha=0.5)
        # print(r)

    print(out)
    plt.xlim(config.MEM_MIN, config.MEM_MAX)
    matplotlib.axes.Axes.set_xscale(1, 'linear')

    plt.plot(out)
    plt.show()

    return out


def parse_rom(rom_path):
    """Parses the ROM and segments into blocks with relative pointer positions"""

    # Open ROM
    rom_fp = os.open(os.path.join(path, rom_path), os.O_RDWR)
    mm = mmap.mmap(rom_fp, 0, prot=mmap.PROT_READ)

    chunk = ""  # Chunk to append blocks to for parsing
    blocks = []
    end = config.MEM_MAX  # Iterator for memory max
    curr = 0
    total = 0
    counter = 0
    while True:
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)

        if table_idx < 1:
            break

        table = mm[table_idx:end].hex()
        table = table[config.HEADER_SIZE:-config.FOOTER_SIZE]  # Remove table header/footer info
        chunk = table + chunk
        print()
        print(len(chunk))
        print(hex(table_idx))
        block = Block(chunk, table_idx + 24)

        # print(len(chunk))

        if not (len(block.pointers) or len(block.seqs)) or len(chunk):
            end = table_idx
            chunk = ""
            curr = 0
            continue

        # Calculate the block's likelihood of being contigious in memory
        eps = 1e-5
        num_ptrs = len(block.pointers)
        num_seqs = len(block.seqs)
        num_blocks = len(chunk) / config.BLOCK_SIZE

        # Ratio of seqs to pointers with exponential falloff: (p/(s+e) - 0.4^n)
        if num_ptrs > 10 and num_seqs > 10:
            tmp = (num_ptrs / (num_seqs + eps))
        else:
            tmp = (num_ptrs / (num_seqs + eps)) - (0.4 ** num_blocks)

        # TODO figure out probabilities associated with each sequence to 
        # assign each to the most likely pointer

        # Calculate the location of mapped memory pointers in ROM
        if tmp <= curr:
            # block = Block(chunk.replace(table, ""), table_idx - config.BLOCK_SIZE + 24)
            block = Block(chunk.replace(table, ""), table_idx + 24)

            # if curr < 0.75 or len(block.pointers) < 8:
            if len(block.pointers) < 8:
                end = table_idx
                chunk = ""
                curr = 0
                continue

            if "seqs" not in block.pointers.columns:
                curr = tmp
                end = table_idx
                continue

            block.pointers["ptr_location"] = block.pointers["text"].map(
                lambda x: mm.find(bytes.fromhex(x), table_idx)
            )
            block.pointers = block.pointers[block.pointers["ptr_location"] > 0]
            blocks.append(block)

            print("MINTED BLOCK")
            print(len(block.pointers), len(block.seqs))
            print("pointers mapped", total)
            print(block.pointers)
            print()

            total += len(block.pointers)
            chunk = ""
            curr = 0
            end = table_idx
            counter += 1
            continue

        curr = tmp
        end = table_idx

    return blocks


def patch_rom(blocks, translation_table):
    out = {}
    out_fp = open("pointer_table.json", "w")
    patched_path = "patched_rom.bin"

    copyfile(rom_path, patched_path)
    patched_fp = os.open(os.path.join(path, patched_path), os.O_RDWR)
    patched_mm = mmap.mmap(patched_fp, 0, prot=mmap.PROT_WRITE)

    counter = 0xffff0000  # Counter for new pointer for translated sequence
    for block in tqdm(blocks):
        for ptr in block.pointers.iterrows():
            location = ptr[1]["ptr_location"]
            pointer = ptr[1]["seqs"]

            new_ptr = bytes.fromhex(utils.reverse_ptr(hex(counter)[2:]))

            patched_mm.seek(location)
            patched_mm.write(new_ptr)

            if pointer in translation_table:
                seq = utils.encode_english(translation_table[pointer])
            else:
                seq = utils.encode_english("null")

            seq.append(0)
            out[str(counter - 0xffff0000)] = seq

            counter += 1

    json.dump(out, out_fp)


def init_translation_table(blocks):
    """Creates a json of all sequences in the blocks for translation"""

    translation_path = os.path.join(path, "data/translation_seq_table.json")

    # If translation table already exists
    if os.path.isfile(translation_path):
        with open(translation_path, "r+") as translation_fp:
            return json.load(translation_fp)

    # Create new translation table
    translation_table = {}
    with open(translation_path, "w+") as translation_fp:
        for b in tqdm(blocks, desc="Patching blocks"):
            for p in b.pointers.iterrows():
                key = p[1]["seqs"]
                val = utils.clean_seq(key)
                val = bytes.fromhex(val).decode("shift-jis", "ignore")
                val = translation.translate(val)

                # print(val["choices"][0]["text"])

                # For each pointer in block add to dialog table
                translation_table[key] = val["choices"][0]["text"]

        json.dump(translation_table, translation_fp, indent=4)

    return translation_table


if __name__ == "__main__":
    rom_path = utils.get_rom_path()

    group_pointers(rom_path)
    # blocks = parse_rom(rom_path)

    # translation_table = init_translation_table(blocks)
    # patch_rom(blocks, translation_table)




    # with open("test_table2.txt", "r") as test_table_fp:
        # chunk = test_table_fp.read()

    # print(len(chunk))

    # blocks = {}
    # chunk = chunk.split("00FFFFFFFFFFFFFFFFFFFF00")
    # chunk = [x.replace("\n", "")[24:config.BLOCK_SIZE] for x in chunk if x]
    # chunk = "".join(chunk)

    # b = Block(chunk, 0)

    # print(b.seqs)
    # print(b.pointers)
