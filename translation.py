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

# generator = pipeline('text-generation', model='EleutherAI/gpt-neo-2.7B')

# prompt = """
# Beautifully poetic translations of English prose to Japanese

# Japanese: わたしは　にほんごがすこししかはなせません。
# English: Unfortunately, I speak only a little Japanese..

# Japanese: わたしは　にほんごがすこししか　はなせません。
# English: I only speak a little Japanese.

# Japanese: どういたしまして。
# English: You're welcome.

# Japanese:"""


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
        null_idx = max(mm.rfind(b"\x71\x1A", 0, end), null_idx)  # NULL separator

        curr = max(min(per_idx, null_idx), min(qst_idx, null_idx))
        # curr = min(max(per_idx, qst_idx), null_idx)

        if ((end - curr) < 300):
            seq = mm[curr:end + 2]  # Sentence
            print()
            print(seq.hex())
            seq = utils.encode_seq(seq).strip()

            # Hash sequence for key
            h_key = hashlib.sha224(seq.encode("utf8")).hexdigest()
            table[h_key] = seq

            # table[h_key] = generator(
                # text_inputs=seq + "\nEnlish: ",
                # prefix=prompt,
                # do_sample=True,
                # max_length=200,
                # return_full_text=False,
            # )
            # )[0]["generated_text"]
            # print("GEn text", table[h_key])


            if "今日も疲れたな。" in seq:
                print(seq)
                print(str(seq.encode("shift-jis", "ignore").hex()))
                print("FUCKK")
                print()
                exit()

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
