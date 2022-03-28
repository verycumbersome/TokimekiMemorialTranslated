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
from itertools import groupby

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
                # Add header length to the address to get correct pointer position
                ptr_location = self.table.index(ptr_text) // 2 + self.address + 24
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

        self.seqs = []
        for seq in self.table.split("00"):
            seq = seq.replace("00", "")

            if utils.check_validity(seq):
                self.seqs.append((self.table.index(seq) // 2, seq))

        self.seqs = pd.DataFrame(self.seqs, columns=["idx", "seqs"])
        self.seqs = self.seqs.drop_duplicates(subset=["idx"])
        self.seqs["seq_location"] = ((self.seqs["idx"] * 2) + self.address).apply(hex)
        # print(self.seqs)

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
        # print(self.pointers)


def group_pointers(filename: str) -> list:
    """Returns a translation table from a bin file"""

    f_ptr = os.open(filename, os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    out = []
    out_idxs = []
    valid_ranges = []
    start = 0
    end = len(mm)

    # # If ranges already exist load from the file
    # if os.path.isfile("sequence_ranges.json"):
        # with open("sequence_ranges.json", "r") as seq_fp:
            # if os.path.isfile("sequence_ranges.json"):
                # return json.load(seq_fp)

    # start = config.MEM_MIN
    # end = config.MEM_MAX
    counter = 0
    while True:
        table_idx = mm.find(config.TABLE_SEP, start, end)
        curr = mm.find(config.TABLE_SEP, table_idx+config.BLOCK_SIZE, end)
        table = mm[table_idx:curr]
        table = table[config.HEADER_SIZE:-config.FOOTER_SIZE]  # Remove table header/footer info

        if (table_idx < 0) or (len(table) != config.BLOCK_SIZE):
            break

        block = Block(table.hex(), table_idx)
        block_value = len(block.seqs)
        counter += block_value
        out.append(block_value)
        out_idxs.append(table_idx)

        print(counter)
        print(hex(table_idx))

        if counter > 10:
            valid_range = table_idx // config.TOTAL_BLOCK_SIZE
            valid_ranges.append(valid_range)

        if counter > 0:
            counter -= 1

        start = curr

    # Get all valid ranges
    output = []
    gb = groupby(enumerate(valid_ranges), key=lambda x: x[0] - x[1])
    all_groups = ([i[1] * config.TOTAL_BLOCK_SIZE for i in g] for _, g in gb)
    valid_ranges = list(filter(lambda x: len(x) > 1, all_groups))
    for r in valid_ranges:
        r = [r[0] - (config.TOTAL_BLOCK_SIZE * 10),
             r[-1]+ (config.TOTAL_BLOCK_SIZE * 10)]
        plt.axvspan(r[0], r[1], color='red', alpha=0.5)
        output.append(r)

    with open("sequence_ranges.json", "w+") as seq_fp:
        json.dump(output, seq_fp)

    return output


def parse_rom(rom_path, min_range, max_range):
    """Parses the ROM and segments into blocks with relative pointer positions"""

    # Open ROM
    rom_fp = os.open(os.path.join(path, rom_path), os.O_RDWR)
    mm = mmap.mmap(rom_fp, 0, prot=mmap.PROT_READ)

    chunk = ""  # Chunk to append blocks to for parsing
    blocks = []

    start = min_range
    end = max_range  # Iterator for memory max

    curr = 0
    total = 0
    while True:
        # table_idx = mm.rfind(config.TABLE_SEP, min_range, end)

        table_idx = mm.find(config.TABLE_SEP, start, end)
        table = mm[table_idx:table_idx + config.TOTAL_BLOCK_SIZE // 2].hex()
        table = table[config.HEADER_SIZE:-config.FOOTER_SIZE]  # Remove table header/footer info
        chunk += table


        # print(table)
        print(hex(table_idx))

        if (table_idx < 0) or (len(table) != config.BLOCK_SIZE):
            break

        block = Block(chunk, table_idx)

        # Calculate the block's likelihood of being contigious in memory
        eps = 1e-5
        num_ptrs = len(block.pointers)
        num_seqs = len(block.seqs)
        num_blocks = len(chunk) // config.BLOCK_SIZE

        print(num_blocks)

        # Ratio of seqs to pointers with exponential falloff: (p/(s+e) - 0.4^n)
        tmp = (num_ptrs / (num_seqs + eps))
        tmp -= (0.4 ** num_blocks) if num_ptrs > 10 and num_seqs > 10 else 0

        # if not (len(block.pointers) or len(block.seqs)) or num_blocks > 40:
            # start += config.TOTAL_BLOCK_SIZE
            # chunk = ""
            # curr = 0
            # continue

        # TODO figure out probabilities associated with each sequence to 
        # assign each to the most likely pointer

        # Calculate the location of mapped memory pointers in ROM
        if tmp <= curr:
            block = Block(chunk, table_idx)

            # if curr < 0.75 or len(block.pointers) < 8:
            if len(block.pointers) < 8:
                start += config.TOTAL_BLOCK_SIZE
                chunk = ""
                curr = 0
                continue

            if "seqs" not in block.pointers.columns:
                curr = tmp
                start += config.TOTAL_BLOCK_SIZE
                continue

            blocks.append(block)

            print("MINTED BLOCK")
            print(len(block.pointers), len(block.seqs))
            print("pointers mapped", total)
            print(block.pointers)
            print()

            total += len(block.pointers)
            chunk = ""
            curr = 0
            start += config.TOTAL_BLOCK_SIZE
            continue

        curr = tmp
        start += config.TOTAL_BLOCK_SIZE

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
            print(ptr)
            location = ptr[1]["ptr_location"]
            pointer = ptr[1]["seqs"]

            new_ptr = bytes.fromhex(utils.reverse_ptr(hex(counter)[2:]))

            patched_mm.seek(location)
            patched_mm.write(new_ptr)

            if pointer in translation_table:
                seq = utils.encode_english(translation_table[pointer])
            else:
                seq = utils.encode_english("null")

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

    # ranges = group_pointers(rom_path)
    blocks = parse_rom(rom_path, config.MEM_MIN, config.MEM_MAX)
    # blocks = []
    # for ran in ranges:
        # blocks += parse_rom(rom_path, ran[0], ran[1])

    # print(blocks)

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
