import hashlib
import subprocess

import translation
import utils

def main():
    trans_table = translation.create_table("/Users/matthewjordan/Library/Application Support/avocado/iso/Tokimeki Memorial - Forever with You (Japan)/Tokimeki Memorial - Forever with You (Japan) (Track 1).bin")

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

                if h_key in trans_table:
                    print("TRANS TABLE", trans_table[h_key])

                tmp = seq


if __name__=="__main__":
    main()
