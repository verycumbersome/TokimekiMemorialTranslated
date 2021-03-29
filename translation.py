import os
import re
import mmap

import hashlib

import utils

def get_table(filename):
    """Returns a translation table from a bin file"""
    # Open hex file
    f_ptr = os.open(filename, os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    # Initialize idx pointer values for all punctuation
    per_idx = mm.rfind(b"\x81\x42", 0, len(mm))  # Period
    qst_idx = mm.rfind(b"\x81\x48", 0, len(mm))  # Question mark
    end = curr = min(per_idx, qst_idx)

    table = {}
    while (curr > 1):
        per_idx = mm.rfind(b"\x81\x42", 0, end)  # Period
        qst_idx = mm.rfind(b"\x81\x48", 0, end)  # Question mark
        null_idx = mm.rfind(b"\x00\x00", 0, end)  # NULL separator

        curr = max(min(per_idx, null_idx), min(qst_idx, null_idx))

        # print("per", per_idx)
        # print("qst", qst_idx)
        # print("nul", null_idx)

        if ((end - curr) < 300):
            seq = mm[curr + 2:end + 2]  # Sentence
            h_key = hashlib.sha224(seq.hex().encode("utf8")).hexdigest()

            table[h_key] = seq.decode("shift-jis", "ignore")

            print(seq.hex())
            print("seq", seq.decode("shift-jisx0213", "ignore"))
            print()
            if "ってるも何も、" in seq.decode("shift-jis", "ignore"):
                print("FUCLKKKK")
                exit()
        end = curr

    return table

if __name__=="__main__":
    get_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")
