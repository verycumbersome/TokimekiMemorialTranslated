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
        seq = p.stdout.readline().strip().split(b" 0 ")[0]
        if (len(seq) > 20):
            if (tmp != seq) and (seq):
                enc_seq = []
                for l in re.split(b'(8142|8148|20)', seq[:-1]):
                    enc_seq.append(l.decode("shift-jis", "ignore")[(len(l) % 4):])

                seq = "".join(enc_seq)
                print("enc", utils.clean_seq("".join(enc_seq)))

                seq = utils.clean_seq(seq)
                seq = utils.read_hex(seq, translate=False)
                h_key = hashlib.sha224(str(seq).encode("utf8")).hexdigest()


                print("DIRECT: ", seq)
                if h_key in trans_table:
                    print("TRANS TABLE: ", translator.translate(trans_table[h_key], lang_tgt='en'))

                print()

                tmp = seq


if __name__=="__main__":
    main()
