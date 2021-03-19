import os
import sys

import tqdm
import mmap

import utils

import subprocess


def main():
    f = os.open("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin", os.O_RDWR)
    mm = mmap.mmap(f, 0, prot=mmap.PROT_READ)

    mm.seek(0x0008F5BC)
    line = mm.readline()

    addr = input()


if __name__=="__main__":
    main()
