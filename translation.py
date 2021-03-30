#!/usr/bin/env python3
import os
import re
import json

import tqdm
import mmap
import hashlib

import utils

def create_table(filename):
    """Returns a translation table from a bin file"""

    # Open hex file
    f_ptr = os.open(filename, os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    # Initialize idx pointer values for all punctuation
    pbar = tqdm.tqdm(total=len(mm))
    per_idx = mm.rfind(b"\x81\x42", 0, len(mm))  # Period
    qst_idx = mm.rfind(b"\x81\x48", 0, len(mm))  # Question mark
    end = curr = min(per_idx, qst_idx)

    counter = 0
    table = {}
    while (curr > 1):
        per_idx = mm.rfind(b"\x81\x42", 0, end)  # Period
        qst_idx = mm.rfind(b"\x81\x48", 0, end)  # Question mark
        null_idx = mm.rfind(b"\x00\x00", 0, end)  # NULL separator

        curr = max(min(per_idx, null_idx), min(qst_idx, null_idx))

        if ((end - curr) < 300):
            seq = mm[curr + 2:end + 2].replace(b"\x00", b"[SEP]")  # Sentence

            # Continue search if shift-jis not valid ascii
            if not ((seq.hex()[:1] == "8") or (seq.hex()[:1] == "9")):
                end = curr
                continue

            # Split sequence for encoding individual sentences
            enc_seq = []
            for l in re.split(b'(\x81\x42|\x81\x48)', seq):
                enc_seq += [s.decode("shift-jis", "ignore") for s in l.split(b"\x20")]

            for seq in "".join(enc_seq).split("[SEP]"):
                if not seq:
                    continue

                # Hash sequence for key
                h_key = hashlib.sha224(str(seq).encode("utf8")).hexdigest()

                # if "あっ、私、野球部でマネージャーをやっている虹野沙希なんだけど。" in seq:
                if "部でマネージャーをや" in seq:
                    print(seq)
                    print(str(seq.encode("shift-jis", "ignore").hex()))
                    print("fuck")
                    # exit()
                seq = str(seq.encode("shift-jis", "ignore").hex())

                # Set table key and val
                table[h_key] = utils.read_hex(seq, translate=False)

        end = curr
        counter += 1
        pbar.update(counter)

    pbar.close()
    return table

if __name__=="__main__":
    with open("translation_table.json", "w") as json_file:
        translation_table = create_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")
        json.dump(translation_table, json_file, indent=4)
