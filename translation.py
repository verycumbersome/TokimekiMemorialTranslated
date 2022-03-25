#!/usr/bin/env python3
"""
All utils for translation and encoding from the ROM hex values
"""

import os
import re
import json

import mmap
import tqdm
import openai
import hashlib

from google_trans_new import google_translator

import utils
import config


# Translation
translator = google_translator()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Globals
path = os.path.dirname(__file__)


def translate(seq):
    """Uses GPT3 to translate japanese text to English"""
    response = openai.Completion.create(
        engine="davinci",
        prompt=config.PROMPT + seq + config.START_SEQUENCE,
        temperature=0.15,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n"]
    )

    return response


def create_table(filename):
    """Returns a translation table from a bin file"""
    table = {}

    f_ptr = os.open(filename, os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    start = 0
    while True:
        table_idx = mm.find(config.TABLE_SEP, start, len(mm))
        curr = mm.find(config.TABLE_SEP, table_idx+config.BLOCK_SIZE, len(mm))

        table = mm[table_idx:curr]
        table = table[config.HEADER_SIZE:-config.FOOTER_SIZE]  # Remove table header/footer info
        table = re.split(b'(\x00\x00|\x80)', table)


        for seq in table:
            if (utils.check_validity(seq)):
                print(hex(table_idx))
                # print(utils.decode_seq(seq))

        if table_idx < 0:
            break

        start = curr

    return table

    # while null_idx > 1:
        # null_idx = mm.find(b"\x00", beg, config.MEM_MAX)  # Null sep
        # curr = mm.find(b"\x00", null_idx, config.MEM_MAX)  # Null sep
        # print(curr)
        # # curr = max(mm.rfind(b"\x71\x1A", 0, end), curr)  # NULL separator

        # seq = mm[beg:curr]  # Sentence
        # seq = utils.decode_seq(seq).strip()

        # print(seq)

        # h_key = hashlib.sha224(seq.encode("utf8")).hexdigest()
        # # if (utils.check_validity(seq) > 0.7) and (h_key not in table):
            # # table[h_key] = {
                # # "seq":seq,
                # # "addr":hex(curr)
            # # }

            # # print("SEQ:",seq)
            # # print()
            # # print(utils.check_validity(seq))

        # end = curr
        # counter += 1

    # print("Table length:", len(table))
    # return table


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
    rom_path = utils.get_rom_path()

    dialog_table = create_table(rom_path)
    # json.dump(dialog_table, open("dialog_table.json", "w"), indent=4)

    # translation_table = translate_table("dialog_table.json")
    # json.dump(translation_table, open("translation_table.json", "w"), indent=4)

    # encode_english("what should i do today?")
    # parse_shift_table("shiftjis_table.txt")
