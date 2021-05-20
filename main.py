#!/usr/bin/env python3
"""
Main function for running the patched game
"""

import os
import re
import json

import hashlib
import subprocess

import utils
import config
import translation

from google_trans_new import google_translator

path = os.path.dirname(__file__)
# if (not os.path.isfile("translation_table.json")):
    # translation.create_table(config.TOKIMEKI_PATH)

# with open(os.path.join(path, "patch/translation_table.json")) as table_fp:
    # trans_table = json.load(table_fp)

OFFSET = 0x62E5198

with open(os.path.join(path, "patch/dialog_table.json")) as table_fp:
    trans_table = json.load(table_fp)

translator = google_translator()


def main():
    p = subprocess.Popen(["./build/release_x64/avocado"],
                         stdout=subprocess.PIPE,
                         cwd="./Avocado")

    tmp = dialog = name = None
    while True:
        seq = p.stdout.readline().lstrip(b"0 ").rstrip(b" \n")
        seq = seq.decode("ascii")

        try:
            if "[NAME]" in seq:
                seq = seq.split("[NAME]")[0]
                seq = bytes.fromhex(seq)
                name = utils.decode_seq(seq)
            else:
                seq = bytes.fromhex(seq)
        except:
            continue

        if (tmp != seq) and (seq):
            seq = utils.decode_seq(seq).strip()
            h_key = hashlib.sha224(seq.encode("utf8")).hexdigest()

            print("DIRECT: ", seq)
            if h_key in trans_table:
                print("NAME: ", name)
                print("TRANS TABLE: ", trans_table[h_key])
                print("HEX", trans_table[h_key]["seq"].encode("shift-jis").hex())
                print("ADDR", hex(int(trans_table[h_key]["addr"][2:], 16) - OFFSET))
                print()
                0x3486a7

            tmp = seq


if __name__=="__main__":
    main()
