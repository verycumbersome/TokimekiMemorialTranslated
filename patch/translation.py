#!/usr/bin/env python3
import os
import re
import json
import time

import tqdm
import mmap
import hashlib

from transformers import pipeline
from google_trans_new import google_translator

import utils

translator = google_translator()


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
            seq = utils.decode_seq(seq).strip()

            if not (check_validity(seq) < 1):
                h_key = hashlib.sha224(seq.encode("utf8")).hexdigest()
                table[h_key] = {
                    "seq":seq,
                    "addr":hex(curr)
                }

                print(hex(curr))

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


def translate_table(filename):
    table = json.load(open(filename, "r"))

    translation_table = {}
    for item in tqdm.tqdm(table):
        try:
            text = translator.translate(table[item], lang_tgt="en")
            translation_table[item] = text
            print(text, end="\r")

        except:
            translation_table[item] = table[item]
            print("banned from google", end="\r")
            continue

    return translation_table


def encode_english(seq):
    # enc = [chr(int(x.encode().hex(), 16) + 0x8220) for x in seq]
    seq = seq.lower()
    enc = "".join([hex(int(x.encode().hex(), 16) + 0x8220)[2:] for x in seq])

    print(bytes.fromhex(enc).decode("shift-jis", "ignore"))



if __name__=="__main__":
    # dialog_table = create_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")
    # json.dump(dialog_table, open("dialog_table.json", "w"), indent=4)

    # translation_table = translate_table("dialog_table.json")
    # json.dump(translation_table, open("translation_table.json", "w"), indent=4)

    # encode_english("what should i do today?")
    parse_shift_table("shiftjis_table.txt")
