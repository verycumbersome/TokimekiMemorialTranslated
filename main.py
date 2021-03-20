import os
import sys
import time


import py
import tqdm
import mmap

import utils

import subprocess

while(True):
    capture = py.io.StdCaptureFD(out=False, in_=False)
    out,err = capture.reset()

    print(out)
    print(err)
    time.sleep(1)


# def main():
    # f = os.open("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin", os.O_RDWR)
    # mm = mmap.mmap(f, 0, prot=mmap.PROT_READ)

    # mm.seek(0x0008F5BC)
    # line = mm.readline()

    # addr = input()


# if __name__=="__main__":
    # main()
