import subprocess

import translation
import utils

def main():
    # trans_table = translation.get_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")

    p = subprocess.Popen(["./avocado"],
                         stdout=subprocess.PIPE,
                         cwd="./Avocado")

    tmp = None
    while True:
        lines = utils.clean_seq(p.stdout.readline().strip()).split(" 0 ")
        for l in lines:
            if (len(l) > 20):
                if (tmp != l) and (l != b""):
                    utils.read_hex(l, translate=False)
                    tmp = l
        print("\n\n")


if __name__=="__main__":
    main()
