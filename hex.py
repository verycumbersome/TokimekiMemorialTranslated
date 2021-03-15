import re
from textwrap import wrap

def read_hex(hexf):
    for l in hexf.split():

        # l = wrap(l, 2)
        # h = [x.encode("latin1").decode("utf-16-le") for x in l]
        # h = [re.findall(r"([一-龯])", x) for x in h]

        l = l.zfill(8)
        h = l.encode("shift_jisx0213").decode("utf_16_le")
        h = re.findall(r"([一-龯])", h)


        print(h)


if __name__=="__main__":
    with open("hex.txt", "r") as hexf:
        read_hex(hexf.read())

