import sys
import time


import py
import tqdm
import mmap

import utils

import subprocess


# while(True):
    # capture = py.io.StdCaptureFD(out=False, in_=False)
    # out,err = capture.reset()

    # print(out)
    # print(err)
    # time.sleep(1)


def main():
    filename = "/Users/matthewjordan/Library/Application Support/avocado/ram.bin"

    addr = int(input(), 16)

    print(utils.read_hex_file(filename, addr))


if __name__=="__main__":
    main()
