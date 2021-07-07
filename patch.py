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
import translation

path = os.path.dirname(__file__)

spinner = Halo(text='Creating blocks', spinner='dots')

# Define globals
rom_fp = os.open(os.path.join(path, config.BIN_PATH), os.O_RDWR)
mm = mmap.mmap(rom_fp, 0, prot=mmap.PROT_READ)


class Block:
    """A block in memory from the ROM separated by the PS1 pointer separator"""

    def __init__(self, table, address):
        self.table = table
        self.address = address

        # Assert correct PS1 block size(4096 bits)
        assert len(table) % config.BLOCK_SIZE == 0, "Incorrect block table length"

        # Initialize class vars
        self.seqs = []
        self.pointers = []
        self.num_pointers = 0

        # Call init functions
        self.get_pointers()
        self.get_seqs()

        if len(self.pointers) and len(self.seqs):
            self.get_offset()
            self.create_ptr_table()

    def get_pointers(self):
        """Get a list of all pointers in a block within a given range"""

        tbl = self.table.replace(" ", "")

        # Extract all potential pointers from table
        tbl = [p[-6:] + "80" for p in self.table.split("80") if len(p) >= 4]

        # Iterate through table and append each pointer to a list
        for ptr_text in tbl:
            ptr = int(utils.reverse_ptr(ptr_text)[2:], 16)

            if ptr > 0x190000 and ptr < 0x19FFFF:  # Make sure pointer location is sufficiently large
                self.pointers.append({
                    "hex": hex(ptr),
                    "text": ptr_text,
                    "idx": ptr
                })

            # Remove all pointers from table
            self.table = self.table.replace(ptr_text, "00000000")

        self.num_pointers = len(self.pointers)
        self.pointers = pd.DataFrame(self.pointers)

    def get_seqs(self):
        """Get sequences and indices from table in ROM"""

        self.seqs = []
        for seq in self.table.split("00"):
            seq = seq.lstrip("0")

            if utils.check_validity(seq):
                self.seqs.append((self.table.index(seq) // 2, seq))

        self.seqs = pd.DataFrame(self.seqs, columns=["idx", "seqs"])
        self.seqs = self.seqs.drop_duplicates(subset=["idx"])
        self.seqs["seq_location"] = self.seqs["idx"] + self.address

    def get_offset(self):
        """Find best offset to match max amount of pointers to sequences"""

        ptr_idxs = np.array(self.pointers["idx"])
        seq_idxs = np.array(self.seqs["idx"])

        self.offset = np.bincount(np.ravel(ptr_idxs[:, None] - seq_idxs[None, :])).argmax()

    def create_ptr_table(self):
        # Apply best offset to the sequence indices and merge given offset
        self.seqs["idx"] += self.offset
        self.pointers = pd.merge(self.seqs, self.pointers, on="idx")


def init_blocks():
    """Parses the ROM and segments into blocks with relative pointer positions"""

    chunk = ""  # Chunk to append blocks to for parsing
    blocks = []
    block_counter = 0
    end = config.MEM_MAX  # Iterator for memory max

    while True:
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)

        if table_idx < 1:
            break

        table = mm[table_idx:end].hex()
        table = table[config.HEADER_SIZE:-config.FOOTER_SIZE]  # Remove table header/footer info

        chunk = table + chunk

        b = Block(chunk, table_idx + 24)

        block_counter += 1

        tmp = Block(table, 0)

        print(hex(table_idx))

        if not len(tmp.pointers):
            end = table_idx
            if block_counter > 24:
                chunk = ""
            continue

        # Get amount of duplicate pointers between main chunk and currect block
        diff = abs(len(np.unique(b.pointers["idx"])) - b.num_pointers)
        if diff > 42:
            if "seqs" not in b.pointers.columns:
                end = table_idx
                continue

            b.pointers["ptr_location"] = b.pointers["text"].map(
                lambda x: mm.find(bytes.fromhex(x), table_idx)
            )
            b.pointers = b.pointers[b.pointers["ptr_location"] > 0]
            blocks.append(b)

            # print(b.pointers)

            block_counter = 0
            chunk = ""

        end = table_idx

    return blocks


def patch_rom(blocks, translation_table):
    patched_path = "patched_rom.bin"

    copyfile(config.BIN_PATH, patched_path)

    patched_fp = os.open(os.path.join(path, patched_path), os.O_RDWR)
    patched_mm = mmap.mmap(patched_fp, 0, prot=mmap.PROT_WRITE)

    counter = 0xffff0000

    out = {}
    for block in tqdm(blocks):
        for ptr in block.pointers.iterrows():
            location = ptr[1]["ptr_location"]
            pointer = ptr[1]["seqs"]

            new_ptr = bytes.fromhex(utils.reverse_ptr(hex(counter)[2:]))

            patched_mm.seek(location)
            patched_mm.write(new_ptr)

            if pointer in translation_table:
                seq = utils.encode_english(translation_table[pointer])
                seq.append(0)
            else:
                seq = "null"

            out[str(counter - 0xffff0000)] = seq

            counter += 1

    ptr_tbl_fp = open("pointer_table.json", "w")
    json.dump(out, ptr_tbl_fp)


def create_translation_table(blocks):
    """Creates a json of all sequences in the blocks for translation"""

    translation_path = os.path.join(path, "data/translation_seq_table.json")

    # If translation table already exists
    if os.path.isfile(translation_path):
        with open(translation_path, "r+") as translation_fp:
            return json.load(translation_fp)

    # Create new translation table
    translation_table = {}
    with open(translation_path, "w+") as translation_fp:
        for b in blocks:
            for p in b.pointers.iterrows():
                key = p[1]["seqs"]
                val = utils.clean_seq(key)
                val = bytes.fromhex(val).decode("shift-jis", "ignore")
                val = translation.translate(val)

                print(val["choices"][0]["text"])

                # For each pointer in block add to dialog table
                translation_table[key] = val["choices"][0]["text"]

                break

            break

        json.dump(translation_table, translation_fp, indent=4)

    return translation_table


if __name__ == "__main__":
    blocks = init_blocks()

    translation_table = create_translation_table(blocks)
    patch_rom(blocks, translation_table)

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
