import subprocess

import utils

def main():
    args = ["./avocado"]
    p = subprocess.Popen(args,
                         stdout=subprocess.PIPE,
                         cwd="./Avocado")
    # p.stdout.flush()

    # Main emulator loop 
    tmp = None
    while True:
        lines = str(p.stdout.readline().strip()).split(" 0 ")

        for l in lines:
            if (len(l) > 20):
                if (tmp != l) and (l != b""):
                    utils.read_hex(str(l), translate=True)
                    tmp = l

        print("\n\n")


if __name__=="__main__":
    main()
