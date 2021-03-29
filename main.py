import os
import json

import hashlib
import subprocess

import translation
import utils

if (not os.path.isfile("translation_table.json")):
    translation.create_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")

with open("translation_table.json") as table_fp:
    trans_table = json.load(table_fp)


def main():
    p = subprocess.Popen(["./avocado"],
                         stdout=subprocess.PIPE,
                         cwd="./Avocado")

    tmp = None
    while True:
        seq = p.stdout.readline().strip().split(b" 0 ")[0]
        if (len(seq) > 20):
            if (tmp != seq) and (seq != b""):
                seq = utils.clean_seq(seq)
                seq = utils.read_hex(seq, translate=False)
                h_key = hashlib.sha224(str(seq).encode("utf8")).hexdigest()

                print("DIRECT: ", seq)
                if h_key in trans_table:
                    print("TRANS TABLE: ", trans_table[h_key])

                tmp = seq


if __name__=="__main__":
    main()
