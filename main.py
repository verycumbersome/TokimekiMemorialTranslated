#!/usr/bin/env python3
import os
import re
import json

import hashlib
import subprocess
from google_trans_new import google_translator

# import translation
import utils

if (not os.path.isfile("translation_table.json")):
    translation.create_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")

with open("translation_table.json") as table_fp:
    trans_table = json.load(table_fp)

with open("dialog_table.json") as table_fp:
    trans_table = json.load(table_fp)

translator = google_translator()


def handle_dup(seq):
    """Takes string sequence and checks for duplicates"""
    dup = seq.split(b" ")
    dup = sum([dup[c] == dup[(c+1)%len(dup)] for c in range(len(dup))])

    if dup > 10:
        seq = b"".join(seq.split(b" ")[::2])

    return seq


def main():
    p = subprocess.Popen(["./avocado"],
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
                # os.system("clear")
                print("NAME: ", name)
                print("TRANS TABLE: ", trans_table[h_key])
                print()

            tmp = seq



if __name__=="__main__":
    main()
