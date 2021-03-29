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
            seq = mm[curr + 2:end + 2].replace(b"\x00", b"")  # Sentence
            seq = seq.replace(b"\x20", b"")
            seq = str(seq.decode("shift-jis", "ignore"))
            h_key = hashlib.sha224(str(seq).encode("utf8")).hexdigest()

            table[h_key] = str(seq)


            # print("seq", str(seq))
            # print(mm[curr + 2:end + 2].replace(b"\x00", b""))
            # print()
            # if "知ってるも何も、超有名人じゃないか。" in str(seq):
                # print("FUCLKKKK")
                # exit()

        end = curr

    return table

if __name__=="__main__":
    get_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")
