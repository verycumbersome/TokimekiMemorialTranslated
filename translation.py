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
import config

translator = google_translator()


def create_table(filename):
    """Returns a translation table from a bin file"""
    f_ptr = os.open(filename, os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    table = {}
    end = per_idx = qst_idx = config.MEM_MAX
    pbar = tqdm.tqdm(total=len(mm))

    counter = 0
    #TODO make sentence search better
    while (per_idx > 1 and qst_idx > 1):
        per_idx = mm.rfind(b"\x81\x42", config.MEM_MIN, end)  # Period
        qst_idx = mm.rfind(b"\x81\x48", config.MEM_MIN, end)  # Question mark

        curr = mm.rfind(b"\x00", config.MEM_MIN, max(per_idx, qst_idx))  # null separator
        curr = max(mm.rfind(b"\x71\x1A", 0, end), curr)  # NULL separator

        if ((end - curr) < 300):
            seq = mm[curr:end]  # Sentence
            seq = utils.decode_seq(seq).strip()

            h_key = hashlib.sha224(seq.encode("utf8")).hexdigest()
            if (utils.check_validity(seq) > 0.7) and (h_key not in table):
                table[h_key] = {
                    "seq":seq,
                    "addr":hex(curr)
                }

                print("SEQ:",seq)
                print()
                print(utils.check_validity(seq))

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


if __name__=="__main__":
    dialog_table = create_table(config.TOKIMEKI_PATH)
    # json.dump(dialog_table, open("dialog_table.json", "w"), indent=4)

    # translation_table = translate_table("dialog_table.json")
    # json.dump(translation_table, open("translation_table.json", "w"), indent=4)

    # encode_english("what should i do today?")
    # parse_shift_table("shiftjis_table.txt")
