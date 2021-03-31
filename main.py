#!/usr/bin/env python3
import os
import re
import json

import hashlib
import subprocess
from google_trans_new import google_translator

import translation
import utils

if (not os.path.isfile("translation_table.json")):
    translation.create_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")

with open("translation_table.json") as table_fp:
    trans_table = json.load(table_fp)

translator = google_translator()


def handle_dup(seq):
    """Takes string sequence and checks for duplicates"""
    dup = seq.split(" ")
    dup = sum([dup[c] == dup[(c+1)%len(dup)] for c in range(len(dup))])

    if dup > 10:
        seq = " ".join(seq.split(" ")[::2])

    return seq


def main():
    p = subprocess.Popen(["./avocado"],
                         stdout=subprocess.PIPE,
                         cwd="./Avocado")

    tmp = None
    while True:
        p.stdout.flush()
        seq = p.stdout.readline().strip()
        try:
            seq = seq.decode("ascii")
            seq = bytes.fromhex(seq[:-1])

        except ValueError:
            continue

        if (len(seq) > 20):
            if (tmp != seq) and (seq):
                seq = utils.encode_seq(seq[:-1])
                h_key = hashlib.sha224(seq.encode("utf8")).hexdigest()


                # print("DIRECT: ", seq)
                if h_key in trans_table:
                    print("TRANS TABLE: ", translator.translate(trans_table[h_key], lang_tgt='en'))
                    print("TRANS TABLE: ", trans_table[h_key])

                print()

                tmp = seq


if __name__=="__main__":
    main()
