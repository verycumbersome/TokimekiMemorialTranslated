#!/usr/bin/env python3
import os
import re
import json
import time

import tqdm
import mmap
import hashlib

import utils

# TODO look over this absolute dogshit code
def trim_seq(seq):
    """Trims a sequence to the earliest valid shift-jis (8-9 first char range) character"""
    idx = 0
    if not ((seq.hex()[:1] == "8") or (seq.hex()[:1] == "9")):
        if "8" in seq.hex():
            idx = seq.hex().index("8")

        elif "9" in seq.hex():
            if seq.hex().index("9") > idx:
                seq = seq[idx:]
            else:
                seq = seq[seq.hex().index("9"):]

    return seq


def create_table(filename):
    """Returns a translation table from a bin file"""

    # Open hex file
    f_ptr = os.open(filename, os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    table = {}
    end = curr = 110000000
    pbar = tqdm.tqdm(total=len(mm))

    counter = 0
    while (curr > 1):
        per_idx = mm.rfind(b"\x81\x42", 0, end)  # Period
        qst_idx = mm.rfind(b"\x81\x48", 0, end)  # Question mark
        null_idx = mm.rfind(b"\x00", 0, end)  # NULL separator

        curr = max(min(per_idx, null_idx), min(qst_idx, null_idx))

        if ((end - curr) < 300):
            seq = mm[curr:end + 2]  # Sentence
            seq = utils.encode_seq(seq)

            # Hash sequence for key
            h_key = hashlib.sha224(seq.encode("utf8")).hexdigest()

            if "はははは、ならないって。じゃあ私、もうひとっ走りしてくるから。" in seq:
                print(seq)
                print(str(seq.encode("shift-jis", "ignore").hex()))
                print("FUCKK")
                print()
                # exit()

            seq = str(seq.encode("shift-jis", "ignore").hex())

            # Set table key and val
            table[h_key] = utils.read_hex(seq, translate=False)

        end = curr
        counter += 1
        pbar.update(counter)

    pbar.close()
    print("Table length:", len(table))
    return table

if __name__=="__main__":
    with open("translation_table.json", "w") as json_file:
        translation_table = create_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")
        json.dump(translation_table, json_file, indent=4)
