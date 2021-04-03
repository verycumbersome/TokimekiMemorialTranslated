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


table_header = """
# start table is @hiragana
# make sure you view this in a font that contains U+3099/U+309A

@main

"""


def parse_shift_table(filename):
    """Parse the shift-jis lookup table"""
    shift_table = open(filename, "r")

    with open("game.tbl", "w") as table:
        table.write(table_header)
        for line in shift_table.readlines():
            line = line.split("#")[0].split("\t")[:2]

            lhs = str(line[0][2:])
            rhs = bytes.fromhex(lhs).decode("shift-jis", "ignore")

            if lhs and rhs and not any(re.findall("<|>", rhs, re.IGNORECASE)):
                table.writelines(lhs + "=" + rhs + "\n")
                print(lhs + "=" + rhs + "\n")


if __name__=="__main__":
    parse_shift_table("shiftjis_table.txt")
