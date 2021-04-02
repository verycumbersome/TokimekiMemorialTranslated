#!/usr/bin/env python3
import os
import re
import json
import time

import tqdm
import mmap
import hashlib

from transformers import pipeline

import utils


def check_validity(seq):
    """Returns proportion of valid shift-jis characters in a string"""
    valid = 0
    for c in seq:
        enc_char = int(c.encode("shift-jis", "ignore").hex(), 16)
        if (0x8140 < enc_char < 0x9FFC):
            valid += 1

    return valid / len(seq)


def create_table(filename):
    """Returns a translation table from a bin file"""
    f_ptr = os.open(filename, os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    table = {}
    end = per_idx = qst_idx = 110000000
    pbar = tqdm.tqdm(total=len(mm))

    counter = 0
    while (per_idx > 1 and qst_idx > 1):
        per_idx = mm.rfind(b"\x81\x42", 0, end)  # Period
        qst_idx = mm.rfind(b"\x81\x48", 0, end)  # Question mark

        curr = mm.rfind(b"\x00", 0, max(per_idx, qst_idx))  # null separator
        curr = max(mm.rfind(b"\x71\x1A", 0, end), curr)  # NULL separator

        if ((end - curr) < 300):
            seq = mm[curr:end]  # Sentence
            seq = utils.encode_seq(seq).strip()

            if not (check_validity(seq) < 1):
                # Hash sequence for key
                h_key = hashlib.sha224(seq.encode("utf8")).hexdigest()
                table[h_key] = seq

                # if "あー、今日も疲れたな。急いで、家に帰ろう。" in seq:
                    # print(seq)
                    # print(str(seq.encode("shift-jis", "ignore").hex()))
                    # print("FUCKK")
                    # print()
                    # exit()

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
